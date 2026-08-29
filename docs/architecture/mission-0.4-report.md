# Mission 0.4 — Completion Report

Sprint: 0 (Foundation)
Mission: 0.4 — Orchestration, RLS, Provider Integration & Evaluation Foundation
Date: 2026-08-29
Status: Complete. Mission 0.5 not started.

> Every item in §40 was **executed**, not reasoned about. The stack was running,
> the database was dropped and rebuilt from empty, and the web client was driven
> against a live gateway. Nothing below is marked as passing on the basis of
> reading code.

---

## 1. What this mission added, in one paragraph

Two isolation layers instead of one; the research orchestrator as a real package
with a persisted job ledger; Anthropic and Gemini behind the gateway with a
normalized error taxonomy and a retry policy that refuses to retry deterministic
failures; an evaluation framework in which cost can never offset quality; a
prompt-injection boundary that is a type rather than a convention; and a typed
web API client. **No research logic exists, and every domain capability is still
blocked** — the orchestrator's honest output today is a plan whose every stage is
`BLOCKED`, each naming the decision that blocks it.

---

## 2. RLS implementation

**ADR-012.** Migration `0003_row_level_security.sql`.

```text
Layer 1   the explicit WHERE workspace_id = %s in every repository query
Layer 2   PostgreSQL row-level security                        (new)
```

Layer 1 was **not** removed, and removing it later would be a regression rather
than a cleanup. The two fail differently on purpose: a forgotten `WHERE` is
caught by the policy, and a connection that never established a tenant context
returns *no* rows rather than *wrong* ones.

### The two obstacles that had to be solved first

Neither is obvious, and either one silently produces a system that looks
protected and is not.

**A superuser and a table owner bypass RLS.** The local stack connects as the
superuser the `postgres` image creates. Enabling policies without addressing that
produces isolation tests that pass while proving nothing — worse than no tests,
because it converts an open question into a false answer.

Resolved with a `NOLOGIN NOSUPERUSER NOBYPASSRLS` role, `sros_app`, assumed per
transaction via `SET LOCAL ROLE`, plus `FORCE ROW LEVEL SECURITY` so the owner is
bound too. `NOLOGIN` means no password exists, therefore none can be committed in
a migration.

**A session-level tenant context leaks through a connection pool.** ADR-005
suggested `SET LOCAL app.workspace_id`; ADR-011 pools connections. A plain `SET`
survives the connection's return to the pool and the next borrower inherits the
previous tenant — a cross-tenant read with no bug in any query, reachable only
under concurrency.

Resolved by making both the role and the context **transaction-local**:

```sql
SET LOCAL ROLE sros_app;
SELECT set_config('app.workspace_id', $1, true);
```

`set_config` with a bound parameter rather than `SET LOCAL … = '…'`, because a
tenant id interpolated into a statement is the one place this system must not
take a shortcut.

### Coverage

| | Count |
|---|---|
| Tenant-scoped tables with `ENABLE` + `FORCE` and one `tenant_isolation` policy | **15** |
| Global tables deliberately without a policy | 6 |

`core.workspace_memberships` carries a `workspace_id` and still gets no policy:
it is the table that will *define* access once authentication exists, and "which
workspaces may this user enter?" is asked before any workspace is chosen. Gating
it on the answer makes the question unanswerable. It is protected by being
read-only to `sros_app`.

The helper fails closed three ways — unset, empty and malformed all resolve to
`NULL`, and `workspace_id = NULL` is not `TRUE`. **There is no fallback
workspace and no `COALESCE` to a default**; a test reads the policy expression to
assert it.

---

## 3. RLS validation

Executed against a real PostgreSQL. 41 tests in
`services/gateway/python/tests/test_rls.py`, every one using **two workspaces** —
a tenancy suite with one workspace cannot detect a missing tenant filter.

| Requirement (§6) | Result |
|------------------|--------|
| Workspace A sees A rows | **PASS** |
| A cannot see B rows | **PASS** |
| B cannot see A rows | **PASS** |
| Missing tenant context returns no rows / fails closed | **PASS** — parameterized over all 15 tables |
| Connection reuse cannot leak previous tenant context | **PASS** — single-connection pool, so the same physical connection is guaranteed |
| Repository filters and RLS agree | **PASS** — same row set through both paths |
| **Direct SQL that forgets `workspace_id` is still protected** | **PASS** |

That last row is why the migration exists. Four cases prove it, and layer 1
cannot help with any of them because the `WHERE` clause is what is missing:

- `SELECT` with no `WHERE` returns only the current tenant's rows;
- an unfiltered `count(*)` is strictly less than the global count;
- an unfiltered `JOIN` across two tenant tables cannot cross the boundary;
- `DELETE FROM research.research_projects` from workspace A leaves B's rows
  intact.

Writes are covered too: a cross-tenant `INSERT` and an `UPDATE` that would move a
row into another workspace are both refused by `WITH CHECK`. `USING` alone would
have allowed a workspace to write a row it could never see — visible to exactly
the wrong tenant.

Also asserted: the application role has neither `BYPASSRLS` nor `SUPERUSER` nor
`LOGIN`. Those are the attributes that make every other test in the file mean
something.

---

## 4. Orchestrator architecture

`services/research-orchestrator/python/sros_orchestrator` — a real package, added
to the uv workspace.

```
lifecycle.py     session status transitions -- the ONLY place they are decided
jobs.py          the generic job description and its ledger states
dag.py           dependency ordering, without a workflow engine
plan.py          the ResearchExecutionPlan and the blocked-capability register
budget.py        configured / reserved / actual accounting and the guard
completeness.py  the Research Completeness record. No formula
repositories.py  persistence over a duck-typed tenant database
orchestrator.py  the coordinator
```

**It imports no database driver and no gateway module.** The repositories take
any object exposing `tenant_transaction(workspace_id)`. That is what keeps the
`service-boundaries.md` §4 graph acyclic while both contexts share one process
in Phase 1 — and it means the orchestrator is fully unit-testable with no stack
running.

**Transition policy moved here (§9).** Mission 0.3 put `ALLOWED_TRANSITIONS` in
`sros_gateway.db.repositories`, which placed a policy decision inside a
persistence layer. The gateway now imports it: one table, not a copy that
drifts. The states themselves are unchanged — Ontology V2 §15 verbatim, and a
test asserts that the table's keys are exactly the contract enum's values so a
state added on one side only cannot enter.

### Why nothing is dispatched

The planner enumerates the pipeline and marks every stage `BLOCKED` with the
decision that blocks it:

| Capability | Blocked by |
|------------|-----------|
| `ACQUISITION` | **D-07** — no source registry, no legal review record |
| `NORMALIZATION` | D-07 — nothing to normalize |
| `NLP_EXTRACTION` | D-12 and §34 |
| `OPPORTUNITY_DISCOVERY` | D-12 — consumes signals nothing produces |
| `SCORING` | **D-03** — the aggregation rules are undefined |

A plan with runnable stages would describe a system that does not exist. **The
guard is mechanical, not remembered:** `BLOCKED` has no permitted transition to
`READY`, and only `READY` jobs are dispatched. There is no code path that can
dispatch blocked work.

The dispatch, retry, resumption and budget machinery is nonetheless real and
tested — exercised with job specs supplied directly by a caller, which is what a
capability will do once unblocked.

### Why not a workflow engine (§12)

Celery already provides the queue, retry, routing and dead-letter path (ADR-004).
What was missing is a dependency list and a rule for when a job becomes runnable:
`dag.py`, about a hundred lines. Adding Airflow or Temporal would buy a UI and a
DSL and cost a second scheduler competing for authority over what runs — the same
objection ADR-004 raised against a dual-queue architecture.

The trigger for revisiting is recorded in the orchestrator README rather than
left as a preference: dynamic fan-out of unknown size, long-running
human-in-the-loop steps, cross-session workflows, or more than one operator. None
is true today; two are plausible within a year, which is why the dependency data
lives in a table rather than in code.

---

## 5. Job persistence model

`research.research_jobs` — the task ledger. **Deliberately generic:** `job_type`
is a string and `payload` is opaque `JSONB`, so adding a job class is an INSERT
rather than a migration. A schema shaped around the first collector needs a
migration for the second.

Fields per §11: `job_id`, `job_type`, `workspace_id`, `research_session_id`,
`correlation_id`, `idempotency_key`, dependencies (a separate edge table),
`queue`, `estimated_cost_units`, `status`, `attempts`.

Two constraints carry weight beyond bookkeeping:

- `UNIQUE (workspace_id, idempotency_key)` — ADR-004 delivery is at-least-once, so
  a duplicate collides on a database constraint rather than on a read-then-write
  check, which is a race with a longer window.
- `CHECK (status <> 'BLOCKED' OR blocked_reason IS NOT NULL)` — an unexplained
  block is indistinguishable from work that was quietly dropped.

`research.research_job_dependencies` holds the edges, with a `CHECK` refusing a
self-edge — the cheapest cycle to create and the easiest to miss. Cycles across
several jobs are detected at **planning** time; a cycle found at dispatch time is
a plan that runs partially and then stalls with no error.

### A real defect the tests found

The first implementation derived the idempotency key from `sros_workers.idempotency_key`,
which hashes task name, workspace and payload — **tenant-separated but not
session-separated**, because it predates the ledger. With a unique constraint on
`(workspace_id, idempotency_key)`, a workspace could hold exactly one job of a
given type and payload *forever*, and the second session to plan the same stage
silently inserted nothing.

Found by a duplicate-delivery test asserting one row and getting zero. The
session is now folded into the hashed material, leaving the worker contract
Mission 0.3 verified untouched. The distinction that matters: two sessions
collecting the same source are not the same unit of work — avoiding a
*re-collection* is a caching decision (`data-principles.md` §12), not an
idempotency one, and conflating them would make freshness impossible to ask for.

---

## 6. Resumability

**There is no in-memory state to restore, which is the design.** Plan, ledger,
dependency edges and budget entries are all in PostgreSQL, because ADR-008 says
Redis is never canonical and progress that lives only in Celery is progress a
broker restart erases.

`resume()` is `advance()` plus one step: jobs left `DISPATCHED` or `RUNNING` by a
dead worker return to `READY` **if they have attempts left**. The reclaim is safe
*because* delivery is at-least-once and every job is idempotent — the worst case
is the work happening twice and the second result colliding on the key. The
attempts guard is what stops a crash loop re-dispatching a poison message
forever.

**Job ids are derived from the idempotency key** (`uuid5`), so a replan after a
crash converges on the ledger that already exists. With random ids, every resume
would insert a parallel copy of the plan and orphan the one in flight.

Verified: a second `ResearchOrchestrator` instance, constructed after the first
was discarded, reads the same ledger and continues. Nothing was checkpointed,
because nothing needed to be.

---

## 7. Cancellation

§14 asked for honesty, and this is where the report earns it.

**What `cancel()` does:** transitions the session to `CANCELLED` where the
lifecycle allows it, and cancels every job not yet handed to a worker, so no
further work is dispatched.

**What it does not do, and does not pretend to:** stop work already running
inside a worker. Celery revocation is advisory, a process mid-HTTP-call does not
observe it, and `task_acks_late` means a killed worker returns the job to the
queue. Claiming instant distributed cancellation would make a caller believe a
resource was freed when it was not.

In-flight jobs are **reported** rather than silently marked cancelled, and their
results are still recorded: a cancelled session that completed three jobs did
three jobs, and hiding that would make the ledger wrong.

Cancelling an already-terminal session is a **no-op, not an error**. Modelling it
as an exception would push every caller into a try/except around a race it cannot
win.

---

## 8. Budget architecture

**Three quantities, deliberately not one** (§15):

```text
configured   the ceiling from the ResearchContext, fixed at session creation
reserved     claimed before dispatch, not yet consumed
actual       really consumed, recorded after the work returns
```

A single `spent` column conflates the last two, and the conflation has a specific
failure: two jobs dispatched concurrently both check the same `actual`, both fit,
and together they overshoot. **Reserving before dispatch is what makes the §16
check hold under concurrency**, and a test proves it — two 10-unit jobs against a
15-unit ceiling produce one dispatch and one refusal.

`research.session_budget_entries` is the ledger: `RESERVATION`, `ACTUAL`,
`RELEASE`. Releases subtract rather than deleting, because an audit that cannot
see a released reservation cannot explain why a session's committed total went
down. `currency` is explicit and defaults to `COST_UNIT` — cost units are
provider-agnostic and are **not** a currency, and recording which is which stops
a later report adding dollars to units.

**Refusal is a successful outcome.** A refused job is not dispatched, the reason
is returned as data fit for a gap report, and the session keeps its status.
**There is no `BUDGET_EXHAUSTED`**, and a test asserts the contract enum does not
contain one.

### Pricing is configuration, and the table is empty

No provider tariff appears in any module, and a test fails the build if one does.
Provider prices change without notice and vary by region and contract; a
plausible constant would be wrong within months and would look authoritative.

**A model with no configured price is UNPRICED, not free**, and the usage record
carries `priced=False`. Reporting an unpriced call as costing zero would show
every budget untouched while real money was spent — which is the failure this
distinction exists to prevent.

---

## 9. Research Completeness representation

§17 said infrastructure only, no formula, and **none was invented**.

`scoring-framework-v1.1.md` §2 gives Research Completeness a purpose and §7 an
illustrative value, and defines no way to compute it. That is the same gap D-03
records for the Evidence Score, and it is left open for the same reason: the
first implementer to pick a number picks it forever, unfalsifiably.

What is enforced is that a value can never be read without its **basis**
(`MEASURED` / `ESTIMATED` / `UNKNOWN`, `NOT NULL` in the schema) and its
**reasons**. An estimate that reads as a measurement is exactly the false
precision §10 forbids, applied to the one number that tells a user how much to
trust everything else.

The rule with teeth, enforced in both the dataclass and the database:

- a session with blocked capabilities **cannot** report `MEASURED` — you have not
  measured what you could not run;
- it cannot report 100 at all;
- blocked capabilities require at least one stated reason.

A fully blocked session therefore records `UNKNOWN` with the reasons naming D-07
and D-03. That is the honest record; a number here would be an invention.

---

## 10. Provider adapters

Anthropic (Messages API) and Gemini (`generateContent`), behind the existing
gateway. **No vendor SDK is imported anywhere**, including inside `providers/`.

Both speak HTTP through an injectable `HttpTransport`. ADR-006 permits an SDK in
`providers/`; using none is stronger and cheaper here:

- `uv.lock` gains no vendor dependency, so a provider's release cadence cannot
  break this repository's install;
- one fake transport is the entire mock surface;
- the request each adapter builds is a plain dict a test asserts on.

The cost, stated: streaming and SDK-provided retry logic must be implemented here
rather than inherited. Neither is needed, and the gateway owns retry policy.

**Structured output uses each provider's decoder constraint** — forced tool use
for Anthropic, `responseMimeType` + `responseSchema` for Gemini — not a prose
"reply in JSON" instruction. A prose instruction competes with every other
instruction in the prompt, including any an attacker placed in a data region. A
decoder constraint does not.

**Neither advertises `EMBEDDING_MODEL`.** Embeddings stay on local BGE-M3;
advertising the tier would let the router send the highest-volume operation in
the system to a paid API.

### Error taxonomy and retry policy (§21, §22)

Both providers map statuses onto the same internal categories — a test asserts
they agree, because a business service branching on `RATE_LIMITED` must get the
same answer from either.

| Category | Retried | Rationale |
|----------|---------|-----------|
| `TIMEOUT`, `RATE_LIMITED`, `TEMPORARY` | yes | A retry can fix it |
| `INVALID_REQUEST` | **no** | Deterministic. The same rejection costs the same twice |
| `AUTHENTICATION` | **no** | Never succeeds, and repeated failed auth trips abuse detection |
| `SCHEMA_FAILURE` | **no** | May signal prompt injection — it surfaces |
| `BUDGET` | **no** | Refusal is the answer |

**Behaviour change, recorded deliberately.** Exhausted retries now propagate the
*original* error with its category, where Mission 0.2 raised
`NoProviderAvailableError`. A timeout reported as "no provider available"
describes a different operational problem from the one that occurred. The
Mission 0.2 test was updated, and its docstring records why rather than being
quietly rewritten.

Credentials never appear in an error message, never in a URL query string
(Gemini uses the header form), and a missing credential fails **before** any
request is sent — asserted.

### Telemetry (§23)

Every request emits a usage record — successes and failures — carrying provider,
model, tier, routing version, prompt id and version, token counts, cost and
pricing version, latency, retries, outcome, error category, and the
`workspace_id` / `research_session_id` / `correlation_id` triple.

**It carries no content.** A test places a secret in a request variable and
asserts it does not appear in the serialized log fields. Telemetry that carried
prompts would put scraped source data into the log pipeline, where
`data-principles.md` §8 says it must never go.

---

## 11. Evaluation framework

[`docs/ai/evaluation-framework-v1.md`](../ai/evaluation-framework-v1.md), added
to the authoritative chain (manifest 1.3).

Datasets are versioned and **declare whether they are synthetic**, and the flag
travels into the run and into the comparison report. A metric over invented
examples measures the machinery; a metric over real labelled data measures the
model. Reporting the first as the second is the same error as reporting an
`ESTIMATED` completeness as `MEASURED`.

**Everything shipped is synthetic** — eight invented statements written to be
unambiguous, the opposite of what a real evaluation set needs. A production set
requires labelled examples from collected sources, and **D-07 blocks
collection**. Building a plausible-looking one instead would produce numbers
worse than none, because they would be quoted.

**Metrics are chosen by the task** (§26). Accuracy is not computed for structured
extraction — it would measure whole-output equality under a name that reads like
partial credit. Classification uses macro-F1, not micro, because `HYPOTHESIS` is
rare and matters most, and a micro average lets a model that never predicts it
score well. Calibration uses the Brier score, the one inverted metric here, which
is why `HIGHER_IS_BETTER` states every metric's direction explicitly.

### Cost cannot offset quality (§27)

`QUALITY_METRICS` excludes cost and latency, and only quality metrics can produce
a regression verdict. A candidate that is cheaper *and* worse is rejected, and
the report says so in a note rather than leaving a reader to notice.

Runs over different datasets, versions or tasks are `INCOMPARABLE` — refusing
beats adjusting, because a delta across different data is wrong in a way that
looks precise.

**Nothing is rolled out.** `ComparisonReport` has no `promote` and no `deploy`,
and a test asserts their absence. `accepted` means *may be considered by a
human*.

---

## 12. Prompt registry

Versioned templates keyed by `(id, version)`. **Lookup requires both**: resolving
"the latest" would let a prompt change alter running behaviour with nothing
recording that it had. Registering the same version twice is refused — a prompt
change is a version bump, not an overwrite.

**The runtime registry is deliberately empty**, and that is not an oversight.
Every context that would own a runtime prompt is blocked or out of scope, so a
classification prompt written now would be written against a signal shape nothing
produces, tested only against its own assumptions, and rewritten the moment real
inputs arrive. The registry is empty; the machinery is real and tested. Same
split the planner makes.

It is also not a place for development prompts: instructions given to a coding
agent are not runtime artifacts and do not belong in the shipped package.

---

## 13. Prompt-injection controls

Three regions, and content can only enter the one it was given:

```text
SYSTEM INSTRUCTIONS          ours, from the template, versioned
TRUSTED APPLICATION CONTEXT  our own data: scope, ids, parameters
UNTRUSTED SOURCE DATA        anything from outside the system
```

**`UntrustedText` is a distinct type, not a convention.** Passing scraped text
where an instruction was expected is a construction error a reviewer can see,
rather than a concatenation that looks identical to a safe one. A bare `str`
cannot enter the untrusted region either — wrapping is what makes provenance
reviewable.

Delimiters inside untrusted content are neutralized, and the neutralization is
**visible**: silently deleting attacker-controlled text hides that an attempt was
made. Labels are neutralized too, because a source can name itself.

Rendering is **deterministic**. Randomised sentinels would be marginally more
robust and would make every replay a different prompt, which would make an
evaluation run incomparable with the one before it.

Six adversarial payloads are tested, including the specific mechanical escape —
emit the closing delimiter, then write what looks like a new instruction turn.
After rendering, exactly one open and one close delimiter survive, and the close
is genuinely last.

**What this does not defend.** Region separation stops the mechanical attacks. It
does **not** make a model immune to persuasion inside a data region, and nothing
does. The defences for that are elsewhere: structured output enforced by a
decoder, a schema failure treated as a possible injection signal rather than
retried, and the rule that an LLM opinion is never observed evidence. Saying so
here is the point — a boundary described as complete is a boundary nobody adds
to.

---

## 14. Web foundation

`apps/web`, Next.js 15 App Router. **The API client and one development page. No
console** — every research capability is blocked, so a dashboard would be a page
of empty panels implying work that cannot run.

**One place builds headers (§31).** `GatewayClient.#headers()` is private and
every method routes through `#request`. When authentication arrives, an
`Authorization` header is added in exactly one method and no component changes.
The temporary workspace header lives in that same method. **No component in the
app knows a workspace exists**, and a test asserts the client exposes no way for
a caller to inject its own headers.

Every request carries a correlation id — generated when the caller supplies none,
and attached to every error type, so a user reporting "it failed" with an id
turns an unreproducible bug into a log query. Every request has a timeout: an
unbounded fetch is a tab that spins forever with no error to report.

Domain enums are **imported** from `@sros/contracts`, never redeclared. A lint
rule refuses a local redeclaration, because a frontend copy of the claims
taxonomy would be wrong only for users.

### A real defect found by running it

`readiness()` documented "returns the payload even on 503" and did the opposite:
`/ready` is the one endpoint that answers a non-2xx with its own body rather than
the gateway's error shape, so a 503 produced `MalformedResponseError` and a
status page had no way to learn *which* dependency was down.

`tsc` could not have caught it — the types were consistent with what the client
*claimed* the server returned. It surfaced on the first run against a live
gateway that happened to answer 503 during startup. Fixed with an explicit
`accept` list, covered by a regression test, and verified against a gateway
pointed at a dead Redis.

That is the Mission 0.3 lesson repeating: **static checking proves the code
agrees with itself.**

---

## 15. Tests

| Suite | Tests | Runner |
|-------|-------|--------|
| Contracts conformance (Python) | 21 | both |
| LLM Gateway (incl. providers, prompts, evaluation, pricing) | 127 (2 skipped, opt-in) | both |
| Celery infrastructure | 21 | both |
| **Orchestration rules (new)** | **56** | both |
| **Gateway integration** (schema, tenancy, API, lifecycle, **RLS**, **orchestration**, **security**) | **147** | pytest |
| **Total Python** | **372** | |
| Contracts conformance (TypeScript) | 19 | `node --test` |
| **Web API client (new)** | **18** | `node --test` |
| **Total** | **409** | |

Mission 0.3 ended at 130 Python + 19 TypeScript.

**225 of the Python tests run with nothing installed** (up from 65), including
the entire orchestration rule set — lifecycle, DAG, budget, completeness. Those
are exactly the rules that must stay checkable when a dependency environment is
broken (ADR-009).

Brief coverage:

| Required | Where |
|----------|-------|
| §35 RLS tenant leakage | `test_rls.py`, 41 tests, two workspaces |
| §35 pooled-connection leakage | `test_rls.py::TestPooledConnectionContext`, single-connection pool |
| §35 missing workspace context | Both suites; parameterized over all 15 tables |
| §35 prompt injection boundary | `test_prompts.py`, 6 adversarial payloads |
| §35 provider SDK import restriction | `test_gateway.py` (tokenized) + ESLint rule; no SDK is even a dependency |
| §35 external error sanitization | `test_security.py` |
| §35 no secret in `/ready` or logs | `test_security.py` |
| §36 all twelve orchestrator cases | `test_orchestration.py` + `test_orchestrator_integration.py` |
| §37 all eight provider cases | `test_providers.py`, both providers |
| §38 all six evaluation cases | `test_evaluation.py` |

### Two testing decisions worth recording

**Schema-constraint probes must not be masked by a policy.** A `NOT NULL` test
inserting `workspace_id = NULL` can never satisfy an RLS `WITH CHECK`, so the
policy fires first and the test stops measuring what it is named after. Those
probes use `privileged_transaction()`, with the reason written beside each one.

**One test reads source rather than behaviour.**
`test_the_repository_still_filters_explicitly` asserts the repository keeps its
`WHERE` clauses, because with RLS enabled the *behaviour* of a query with and
without its tenant filter is identical — which is exactly how a deleted filter
would go unnoticed until someone ran a report with a privileged role.

---

## 16. CI

| Job | Change |
|-----|--------|
| `contracts` | Now runs 225 zero-dependency tests, up from 65 |
| `schema` | 21 tables, 8 invariant groups |
| `typescript` | **Added:** web typecheck, web API client tests, `next build` — a type error must fail the build, and `next build` typechecks generated route types the project-level check cannot see |
| `python-quality` | ruff + `mypy --strict` over 58 source files |
| `integration` | Five packages including the RLS suite. **Added:** an explicit assertion that no provider credential is present and the smoke flag is off |
| `compose` | unchanged |

**No provider key reaches CI, and it is asserted rather than trusted.** A smoke
suite that quietly became enabled would report its problem as an invoice, weeks
later, rather than as a red build.

ESLint now covers `**/*.tsx` as well as `**/*.ts`. The React components are the
newest code in the repository and would otherwise have been the only code exempt
from the architectural rules.

Still not enabled, with reasons unchanged: CodeQL, and a live-provider job.

---

## 17. New issues and decisions

Classified per §29 and the brief's stop condition. **No new domain-level or
schema-shaping contradiction was found, so nothing triggered a stop.**

### Architectural — resolved by ADR, as §29 directs

| Item | Resolution |
|------|-----------|
| Row-level security design | **ADR-012.** Completes ADR-005 §Future row-level security. Supersedes ADR-008's "RLS is designed for but not enabled"; everything else in ADR-008 stands |

### Specification amendments

| Change | Authority |
|--------|-----------|
| `PROJECT_MANIFEST.md` → 1.3: evaluation framework added to the authoritative chain | Mission 0.4 §24. `llm-reasoning-rules.md` §10 requires evaluation datasets and defines none; leaving the document that specifies them outside the chain would put it where the boot sequence never looks |
| `docs/CLAUDE.md` → 1.3: boot sequence gains it; the tenancy invariant records the two layers | Same |
| `service-boundaries.md` → 1.3, `quality-gates.md` → 1.3, `testing-strategy.md` → 1.3 | Consequential |

**No accepted ADR was edited.** ADR-001 through ADR-011 are byte-identical, as
are the superseded specifications (5224 / 10888 / 3582 bytes) and every
historical mission report.

**Numbering note:** the ADR index had reserved ADR-012 for the production
deployment target — a placeholder row with no file and no decision. The number
went to the first ADR actually written; the placeholder is now ADR-013.
Renumbering a TODO breaks no reference and supersedes nothing.

### Defects found and fixed

1. **The idempotency key was not session-separated** (§5). A workspace could hold
   one job of a given type and payload forever, and a second session planning the
   same stage silently inserted nothing. Found by a duplicate-delivery test
   asserting one row and getting zero.
2. **`readiness()` raised on 503 instead of returning the dependency report**
   (§14). Found by running the client against a live gateway; unreachable by
   typechecking.
3. **`DISPATCHED → SUCCEEDED` was forbidden.** A progress event is another
   at-least-once message, so a dropped "started" event would have permanently
   blocked the success report for work that actually completed, leaving the job
   stuck in flight forever. The edge is now allowed, with the reasoning next to
   it.
4. **A self-defeating test.** A guard scanning the smoke-test source for banned
   model-name substrings always failed, because its own list of forbidden tokens
   lived in the file it scanned. Replaced with an assertion on the behaviour: a
   smoke test with no model named skips rather than probing a guess.

### Implementation-local, decided and documented

| Choice | Rationale |
|--------|-----------|
| Provider adapters over raw HTTP, no vendor SDK | No vendor dependency in `uv.lock`; one fake transport is the whole mock surface; the built request is assertable |
| `NOLOGIN` application role rather than a login role with a password | No password exists, therefore none can be committed in a migration. The production path is recorded in ADR-012 §Deployment |
| Evaluation results as JSON files, not a table | They describe the system, not a workspace; a `workspace_id` would attach a meaning they do not have |
| Evaluation lives inside `packages/llm-gateway` | It evaluates LLM components and depends on the gateway's types. A fifth package would add lockfile churn for no boundary |
| `expires_at` on the orchestration tables | `data-retention-policy-v1.md` §2.5 governs operational data (90 days for jobs, §2.2 for session state). Computed at write time by a column default |

### Recorded gaps, not decisions

- **A superuser still bypasses RLS.** `FORCE` binds the owner, not a superuser.
  Anyone connecting as one sees every workspace. Unavoidable, and it is why
  layer 1 remains.
- **Redis AOF durability under a hard kill is still untested.** Carried forward
  from Mission 0.3 §14, unchanged.
- **The circuit breaker has manual open/close hooks and no automation.** Nothing
  counts consecutive failures yet.
- **`/ready` returned a transient 503 shortly after startup** during the web
  verification, then recovered. **Not reproducible:** three further cold starts,
  each hitting `/ready` immediately after `/health` first answered, all returned
  200 with both dependencies `ok`. The original occurrence was one second after a
  process start that followed a database drop and recreate, so a momentary
  dependency hiccup is the likely cause, but it is unconfirmed.

  Recorded rather than closed. It exposed defect 2 above, which is the useful
  outcome; the transient itself remains unexplained, and three passing runs are
  not evidence that it cannot happen again.

---

## 18. Remaining blockers

| ID | Item | Blocks |
|----|------|--------|
| **D-03** | Evidence aggregation formula, recency behaviour, independence thresholds | **`services/scoring` — hard blocker.** Guards active in the schema validator, both contract suites, and now the planner |
| **D-07** | Source registry contents and legal review | `services/acquisition`. `registry.sources` remains a stub |
| **D-12** | Embedding model versioning and re-embedding | `nlp`, and therefore opportunity discovery |
| **A-12** | Non-geographic (segment) scoping | Untouched. A `SEGMENT` scope is still rejected with a message naming A-12 |
| **D-08** | Score recomputation policy | — |
| **D-11** | Observability stack | Conventions implemented; vendor open |
| — | Opportunity identity resolution | Untouched. No matching helper exists |
| — | Production hosting (ADR-013), GDPR/jurisdiction | Untouched. Both require human decision |

Every blocker open at the start of this mission is still correctly open. **None
was resolved by implication.**

---

## 19. Validation commands and results

All executed in this environment, against the running stack, with the database
**dropped and recreated from empty** first.

```bash
docker compose -f infrastructure/compose/docker-compose.yml ps
uv run python infrastructure/scripts/migrate.py --apply --seed
uv run python infrastructure/scripts/migrate.py --apply
python packages/contracts/tools/generate.py --check
python infrastructure/scripts/validate_schema.py
python infrastructure/scripts/run_python_tests.py
uv run python infrastructure/scripts/run_pytest_suites.py
uv run ruff check . && uv run ruff format --check .
uv run mypy packages/... services/...
pnpm exec eslint .
pnpm exec tsc --noEmit -p packages/contracts/tsconfig.json
pnpm --filter @sros/web exec tsc --noEmit -p tsconfig.json
node --test --experimental-strip-types packages/contracts/test/conformance.test.ts
node --test --experimental-strip-types apps/web/test/api-client.test.ts
pnpm --filter @sros/web build
uv run uvicorn "sros_gateway.app:create_app" --factory --port 8412
node --experimental-strip-types apps/web/src/lib/api/smoke.ts
```

| Check | Result |
|-------|--------|
| Docker stack healthy | **PASS** — 3/3 |
| Migrations apply to an **empty** database | **PASS** — 0001, 0002, 0003 |
| Migrations idempotent on re-run | **PASS** — 3 skipped, 0 applied |
| Schema after migration | **PASS** — 6 schemas, 21 tables, 45 FKs, 190 CHECKs, 61 indexes |
| RLS enabled and forced | **PASS** — 15 policies, 15 forced tables |
| Seed | **PASS** — 2 workspaces, 19 registry entries |
| Contract generation current | **PASS** — 3 artifacts |
| Schema invariants (ADR-008) | **PASS** — 8 groups, 21 tables |
| Zero-dependency Python suites | **PASS** — 225 tests, 4 packages |
| pytest suites | **PASS** — 372 tests, 5 packages, 2 skipped (opt-in) |
| Two-workspace RLS tests | **PASS** — 41 tests |
| Orchestrator lifecycle tests | **PASS** — 56 rule tests + 43 integration |
| Execution state survives a restart | **PASS** — second instance continues from the ledger |
| No blocked work dispatched | **PASS** — a full pass over a real plan dispatches nothing |
| Provider adapters, fake transport | **PASS** — 29 tests, both providers, no key |
| No provider key needed anywhere | **PASS** — no test requires one; 2 opt-in tests skip |
| No provider SDK outside `providers/` | **PASS** — none is even a dependency |
| Evaluation run and regression comparison | **PASS** — 34 tests |
| ruff check + format | **PASS** — 158 files |
| `mypy --strict` | **PASS** — 58 source files |
| ESLint (incl. `.tsx`) | **PASS** — 0 errors, 0 warnings |
| `tsc` contracts + web | **PASS** |
| TypeScript conformance | **PASS** — 19 |
| Web API client tests | **PASS** — 18 |
| `next build` | **PASS** — 3 routes, static |
| Web client against a live gateway | **PASS** — health, readiness, project and session creation, canonicalization (`fr` → `FR`), `not_found` handling |
| CI YAML parses | **PASS** — 6 + 3 jobs |
| No BullMQ | **PASS** — 0 occurrences |
| No stale `ResearchRun` | **PASS** — only comments saying it does not exist |
| D-03 forbidden names | **PASS** — only in the guard list itself |
| Accepted ADRs unmodified | **PASS** — ADR-001…011 unchanged |
| Superseded specs unmodified | **PASS** — 5224 / 10888 / 3582 bytes |

**Nothing is reported as NOT VERIFIED.**

---

## 20. Explicit answers

### Is PostgreSQL RLS active?

**Yes.** 15 tenant-scoped tables carry `ENABLE` + `FORCE ROW LEVEL SECURITY` and
one `tenant_isolation` policy each, verified against a database built from empty.
`/ready` reports it (`rls_policies: active`), so the state is observable from
outside rather than assumed.

### Can direct SQL without a workspace filter leak another workspace?

**No.** A `SELECT` with no `WHERE`, an unfiltered `count(*)`, an unfiltered
`JOIN` and a `DELETE` with no `WHERE` were all executed under a tenant context
and none crossed the boundary. This is the case layer 1 cannot help with, and it
is the reason the migration exists.

Caveat, stated because it is real: **a superuser bypasses the policy.**
Administrative access and psql sessions see everything, which is why the
repository filter remains mandatory.

### Can pooled connections leak workspace context?

**No.** Both the role and the tenant context are transaction-local. Tested with a
single-connection pool, so the same physical connection is guaranteed reused:
after a commit the context is `NULL` and the role is back; after a rollback the
same; a second tenant replaces rather than inherits.

### Is ResearchSession execution state persisted?

**Yes.** Plan, job ledger, dependency edges, attempts, timestamps, correlation
id, idempotency key and budget entries are all in PostgreSQL. A test reads every
field the scheduler needs directly from the database with no broker involved.

### Can orchestration resume after restart?

**Yes.** A second orchestrator instance, constructed after the first was
discarded, reads the same ledger and continues. Work left in flight by a dead
worker returns to `READY` if attempts remain, and does not if they do not — which
is what stops a crash loop re-dispatching a poison message.

### Are blocked D-07 and D-03 stages prevented mechanically?

**Yes.** The planner marks them `BLOCKED` with the deciding reference, `BLOCKED`
has no permitted transition to `READY`, and only `READY` jobs are dispatched. A
full scheduling pass over a real plan hands nothing to any queue. The database
additionally refuses a `BLOCKED` row with no stated reason.

### Are Anthropic and Gemini isolated behind the LLM Gateway?

**Yes, and more strongly than required.** `LlmRequest` still has no provider and
no model field. No vendor SDK is imported anywhere — not even inside
`providers/` — so there is no SDK that *could* leak. Business services request a
tier; the tier → provider → model mapping is configuration.

### Can CI run without provider API keys?

**Yes.** No test requires one. The two real-provider smoke tests skip unless
**both** `SROS_ENABLE_PROVIDER_SMOKE_TESTS=1` and a credential are set, the guard
itself is tested, and the integration job asserts that no credential is present.

### Is the evaluation framework operational?

**Yes.** It loads a versioned dataset, runs a model, computes per-task metrics,
stores a result, reloads it and compares two runs — 34 tests, no network.

**What it has not done is measure anything.** Every shipped dataset is synthetic
and says so, and the flag travels into the comparison report. Real datasets need
labelled examples from collected sources, which D-07 blocks.

### Can prompt/model regressions be measured?

**Yes.** `compare_runs` returns `IMPROVED`, `UNCHANGED`, `REGRESSED` or
`INCOMPARABLE` against a configurable tolerance. **A cheaper, worse candidate is
rejected**, and the report says so explicitly rather than leaving a reader to
notice. Nothing is rolled out: the report has no `promote` and no `deploy`.

### Is prompt-injection separation enforced?

**The mechanical half, yes.** Untrusted content is a distinct type that cannot
occupy the system or trusted regions, delimiters inside it are neutralized
visibly, hostile labels cannot open a region, and six adversarial payloads are
tested including the delimiter escape.

**Persuasion inside a data region is not defended, and cannot be.** The defences
for that are structured output enforced by a decoder, a schema failure treated as
a signal rather than retried, and the rule that an LLM opinion is never observed
evidence.

### Does the web application have a typed API foundation?

**Yes,** and it was verified against a live gateway rather than only typechecked
— which is how the `readiness()` defect was found. Headers are built in one
place, no component knows a workspace exists, every request carries a correlation
id and a timeout, and domain enums are imported rather than redeclared.

### Are scoring and acquisition still correctly blocked?

**Yes.** D-03 and D-07 are unresolved. No aggregation, no decay, no thresholds,
no collector. `registry.sources` remains a stub with no `retention_override`. The
guards in the schema validator and both contract suites still pass, and the
planner now adds a third: those stages cannot be dispatched at all.

### Is the system ready to leave Sprint 0?

**Not yet, and the reason is not this mission's work.**

The foundation is done: contracts, storage, runtime, tenancy in two layers,
orchestration, provider access, evaluation and a web boundary. Every
infrastructure question Sprint 0 set out to answer has an answer that was
executed rather than reasoned about.

What remains is not foundation work. **D-07 and D-03 are decisions, not
implementations**, and neither can be resolved by writing code:

- **D-07** needs a source registry with per-source legal review records — an
  answer about terms, licensing and retention for each source, which is human and
  partly legal work.
- **D-03** needs an evidence aggregation framework. `scoring-framework-v1.1.md`
  §13 forbids implementing scoring until it exists, for the reason it states:
  whoever implements first chooses constants that become load-bearing and
  unfalsifiable.

Sprint 1 cannot deliver research output without both. It can deliver either the
source registry or the aggregation framework as a **specification** mission,
which is what the next mission should be — and the orchestrator is already shaped
to unblock a capability by deleting a row from `BLOCKED_CAPABILITIES`.

The GDPR and jurisdiction analysis (`data-retention-policy-v1.md` §7) and the
production hosting ADR remain open and remain human decisions.

---

## 21. Mission boundary

**Mission 0.5 was not started.** No collectors, no NLP, no embeddings, no
clustering, no scoring, no evidence aggregation, no market or competitor
analysis, no GTM generation, no authentication, no dashboard.

A-12 was not resolved. Opportunity identity resolution was not decided. The
source registry was not populated. No production hosting decision was made. No
GDPR policy was finalized. No real evaluation dataset was created, and no
provider was called.
