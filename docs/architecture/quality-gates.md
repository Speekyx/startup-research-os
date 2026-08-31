# Quality Gates

Version: 1.9
Status: Active. Every gate in §1 runs in CI
Date: 2026-08-30 (amended in Mission 1.5)

What must be true for a change to reach `main`. `docs/CLAUDE.md` §Definition of
done is the requirement; this document is the mechanism.

The organising principle: **a rule that is only in a document is a rule that will
be broken.** Every specification obligation that can be moved into a type, a lint
rule, a schema, or a test should be.

---

## 1. Gate summary

| Gate | Tool | Status | Blocking |
|------|------|--------|----------|
| Formatting | Prettier (TS/MD/JSON/YAML), ruff format (Python) | Scaffolded | Yes |
| Lint | ESLint, ruff | Strategy fixed, config pending | Yes |
| Types | `tsc --noEmit`, `mypy --strict` | Config scaffolded | Yes |
| Unit tests | Vitest, pytest | Pending | Yes |
| Contract tests | Schema validation against fixtures | Pending | Yes |
| Integration tests | pytest + testcontainers | Pending | Yes |
| E2E | Playwright | Pending | Nightly, not per-PR |
| Secret scan | gitleaks | Pending | Yes |
| Dependency audit | `pnpm audit`, `pip-audit` | Pending | Warn, then block |
| Diagram/doc sync | Manual (review checklist) | Active | Review |
| Spec compliance | Manual (PR checklist) | Active | Review |

"Pending" means the strategy below is decided and the tool is installed in
Mission 0.2. Nothing in this table is undecided.

### Status as of Mission 0.4

Every gate above now runs. What changed since the table was written:

| Gate | Now |
|------|-----|
| Lint | **Active.** ruff (11 rule families) and ESLint 9 with type-aware rules over `**/*.ts` **and `**/*.tsx`** — the React components are the newest code in the repository and would otherwise be the only code exempt from the architectural rules |
| Types | **Active.** `mypy --strict` over 58 source files; `tsc` over two projects (contracts, web) plus `next build`, which typechecks generated route types the project-level check cannot see |
| Unit / integration tests | **Active.** 225 zero-dependency tests, 370 pytest tests across five packages, 19 TypeScript conformance tests |
| E2E | Still not implemented. There is no user workflow to walk through |

### Gates added in Mission 0.4

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Tenant isolation, two workspaces** | `services/gateway/python/tests/test_rls.py` | A query with no `WHERE workspace_id` returns only the current tenant's rows. This is the one gate that catches a *forgotten* filter rather than a wrong one (ADR-012) |
| **Pooled-connection tenant leak** | Same suite, single-connection pool | A session-level `SET` would leak a tenant between borrowers with no bug in any query |
| **No hard-coded provider tariff** | `test_pricing_and_telemetry.py` | A price constant in a module is a decision nobody recorded making (§15). Fails the build if one appears outside `pricing.py` |
| **No content in telemetry** | Same suite | A secret placed in a request variable must not appear in the serialized log fields (`data-principles.md` §8) |
| **Prompt-injection boundary** | `test_prompts.py`, adversarial payloads | No arrangement of attacker-controlled text escapes its region or reaches the system field (`llm-reasoning-rules.md` §7) |
| **No provider credential in CI** | `ci.yml`, integration job | A smoke suite that quietly became enabled would show up as an invoice rather than as a red build (§20) |
| **Retry policy by category** | `test_providers.py` | An authentication error or an invalid request is never retried: it costs the same twice and trips abuse detection (§22) |
| **Blocked work cannot be dispatched** | `test_orchestrator_integration.py` | A `BLOCKED` job has no transition to `READY`, so the source gate and D-03 hold mechanically rather than by memory (§32, §33) |

### Gates added in Mission 1.0

Every one of these guards a rule that would otherwise depend on a reviewer
remembering it under pressure to ship a collector.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **No approval without authoritative evidence** | `registry.require_evidence_for_approval` (deferred constraint trigger) + `test_source_registry.py` | An approving review with no first-party document is refused at COMMIT, whoever writes it. A blog post cannot be recorded as the basis of an approval, because the evidence-type enum has no value for one |
| **No collector on an ineligible source** | `registry.require_eligibility_for_collector` (BEFORE UPDATE trigger) | Even a direct `UPDATE` by the migration role cannot turn a collector on. The database, not the application, has the last word |
| **The Python gate and the SQL view agree** | `test_source_registry.py` | The eligibility rules exist twice by necessity. Two implementations of one rule drift; this compares them on every source rather than trusting they match |
| **No credential in the registry** | `sros_acquisition.registry.models` + `validate_source_registry.py` + `test_source_registry.py` | `secret_references` holds configuration key names. A value that looks like a credential is refused, so a secret cannot reach a file every reader of the repository can open |
| **No source silently approved** | `validate_source_registry.py` (zero dependency) | Runs with no database and no packages installed. A broken environment cannot reduce this check to nothing (ADR-009 rationale) |
| **Silence is not permission** | `validate_source_registry.py` check 12; `test_new_source_compliance.py` | An approving review must GRANT every activity the assessed use requires. Mission 1.7 approved a source with four of six unaddressed; the prose rule had existed since Mission 1.0 and nothing read it |
| **An approved API profile can actually be reached** | `test_gdelt_readiness.py` | The host allowlist is DERIVED from `access_profiles[].endpoint_url` so revoking a profile revokes the host. Both GDELT profiles recorded no endpoint, so the derived allowlist was empty and no request could ever have been made — asserted on the derived value, which is what the transport is handed |
| **A direct grant is not a way past a licence allowlist** | `test_rights_basis.py`; `compliance/resources.py` | A resource records what KIND of thing authorises it. World Bank's allowlist now requires `NAMED_LICENCE` *and* a matching identifier, where it previously required only the identifier — a descriptor with no basis used to pass (ADR-018) |
| **No fabricated licence identifier** | `AuthorizedDataset.__post_init__`; `test_rights_basis.py` | `DIRECT_GRANT` refuses a licence string in both directions. GDELT names no licence, and "OTHER"/"NONE"/"GDELT Terms Licence" would each land an invented fact in every authorised record's provenance |
| **CI never needs GDELT** | committed fixtures; `capture_gdelt_fixtures.py` is not run in CI | The capture tool runs wherever GDELT is reachable and writes fixtures; CI parses what is committed. Availability of a third party must not decide whether the build passes |
| **The rendered catalog matches the JSON** | `sros-source render --check` | Two hand-maintained copies of one fact drift, and the drift is found by whoever trusted the wrong one |
| **CI calls no external platform** | `ci.yml` | A registry job that fetched a platform's terms would be collection, and would make the build depend on a third party's uptime (§43) |
| **Acquisition blocking is registry-derived** | `test_orchestrator_integration.py` | The orchestrator must read its refusal from `registry.source_eligibility`, not restate it in code. A hardcoded reason is a reason nobody notices going false |

### Gates added in Mission 1.1

D-03 is resolved at the framework level, so the old blanket ban on aggregation
vocabulary was replaced rather than deleted. These gates draw the line that
replaces it.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Rejected designs stay rejected** | `validate_evidence_aggregation.py` | `contradiction_penalty`, `decay_weight`, `aggregated_evidence_score`, `independence_threshold_result`, `evidence_aggregate` are forbidden everywhere, permanently. Each names a design the framework considered and rejected, so its return is a regression rather than an unblocked feature |
| **V1 vocabulary stays out of production surfaces** | Same script | The authorised names are allowed in the reference package and the contracts, never in a migration or under `services/`. Defining the framework and enabling production scoring are separate gates |
| **No universal half-life** | Same script | A module-level half-life constant is refused anywhere. §9 puts half-lives in versioned profiles; a constant would be the invented universal value, and it would *work*, which is what makes it dangerous |
| **No per-source reliability weight** | Same script + `test_evidence_aggregation.py` | No registered source id appears in the aggregation package. Two evidence sets differing only in `source_id` must produce identical numbers |
| **The shipped profile stays UNCALIBRATED** | Same script | Promotion to `CALIBRATED` requires the calibration plan to have been executed and published. A profile cannot even be constructed as `CALIBRATED` without a `calibration_dataset_ref` |
| **`services/scoring` has no implementation** | Same script | The directory is a boundary README. Code appearing in it means production scoring started without a calibrated profile |
| **The twelve mathematical invariants** | `test_evidence_aggregation.py` | Masses sum to 1; the score stays on 0–100; duplicates cannot inflate; unknown independence cannot stack; adding contradiction cannot raise the score; reordering changes nothing; evergreen evidence does not decay; missing inputs are never defaulted |
| **Aggregation is order-independent end to end** | Same suite | Byte-identical canonical output under reordering. Floating-point addition is not associative, so this is engineered by sorting rather than assumed — and it caught a real defect in the explanation serialisation |
| **The sensitivity report matches the code** | `sensitivity --check` | The report is generated from the implementation, so it cannot describe behaviour the code does not have |

### Gates added in Mission 1.2

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Cross-tenant references are impossible, not merely forbidden** | Composite foreign keys carrying `workspace_id` (migration 0005) + `test_claims.py` | A claim cannot reference an opportunity in another workspace, evidence cannot reference a claim in another workspace, and an independence group cannot span claims or workspaces. A third layer under the repository filter and the RLS policy, failing differently from both |
| **The independence shape holds without the repository** | `evidence_independence_shape_check` | `KNOWN_DEPENDENT` must name a group, the other two must not. A future writer that bypasses the repository still cannot store an incoherent record |
| **Unknown independence stays unknown in storage** | Same CHECK + `test_claims.py` | The engine builds its conservative runtime bucket without writing one. An unresolved question must not look resolved in the database |
| **The claim revision pointer names a real revision** | Deferred composite foreign key | A pointer to a nonexistent revision would make the current statement unreadable |
| **RLS on every new tenant table** | Migration 0005 + `test_rls.py` + `test_claims.py` | Four new tables, all ENABLE and FORCE, all policy-bearing. A claim visible across workspaces would leak what another tenant is researching, in their own words |
| **No service imports the reference aggregation engine** | `validate_evidence_aggregation.py` | Tests may import it; production modules may not. This is what makes the vocabulary narrowing below safe (ADR-014) |
| **Computed aggregation values stay out of production** | Same script | The guard was NARROWED, not weakened: evidence INPUT fields became legitimate schema columns in Mission 1.2, while the strengths, masses and score remain forbidden in migrations and under `services/` |
| **No aggregation result is persisted** | `test_claims.py` | Storing a result would be scoring, and scoring requires a `CALIBRATED` profile that does not exist |

### Gates added in Mission 1.3

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **An approving review is still blocked by unsatisfied conditions** | `evidence_independence`-style CHECK plus the eligibility view and `evaluate_eligibility` | `APPROVED_WITH_CONDITIONS` must never quietly mean "a collector may run". Three sources are approving and none is eligible |
| **A catalog load cannot satisfy its own conditions** | `load_catalog_into` never writes `satisfied`; `test_source_review.py` forces every condition false, re-loads, and asserts none was set | A catalog that could declare its own conditions met would make the state meaningless |
| **A satisfied condition must name who and when** | `source_review_conditions_satisfaction_provenance_check` | "Satisfied by nobody, at no time" is the shape an accidental UPDATE leaves behind |
| **Review history is preserved, not overwritten** | Append-only review versions; `test_source_review.py` | The record that matters is "Mission 1.0 concluded X, Mission 1.3 found Y, because document Z became available" |
| **A changed verdict cites evidence retrieved for it** | `test_source_review.py` | A status change with no document behind it is an opinion |
| **Duplicate review versions are refused** | `load_catalog` | Two reviews sharing a version cannot be told apart, and the later would shadow the earlier |
| **The review-results document matches the catalog** | `render_review_results.py --check` | Generated diff view; two hand-maintained copies of one fact drift |
| **The coverage matrix matches the catalog** | `render_signal_coverage.py --check` | Answers "twenty economic sources and no entertainment sources?" from the registry. An answer nobody regenerates is an answer about last month |
| **A suite cannot silently change the registry** | `testing/registry_state.py`, run by `run_pytest_suites.py` | `registry.*` carries no `workspace_id`, so the tenant leak check cannot see it *by construction*. Compared by CONTENT: flipping `collector_enabled` inside a row moves no row count |
| **No collector exists** | `test_source_review.py` | No data-fetching client, no collector module. The day somebody adds one, this fails |

### Gates added in Mission 1.4

Conditions became clearable, which turned the last step between a review and a
collector from "nothing can set this" into "something must". These gates decide
what that something is allowed to be.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A condition cannot be satisfied without a verification** | `registry.require_verification_for_satisfied_condition` (BEFORE trigger, migration 0007) | The SQL bypass, closed. A boolean set by hand — by a migration, an `UPDATE`, a fixture or a developer in a hurry — leaves no record of what was checked. Clearing back to false stays unguarded: failing closed must never need permission |
| **`UNKNOWN` is never promoted to `SATISFIED`** | `satisfied_condition_keys` + `test_compliance.py` | "The verifier failed" and "there is no verifier" are different problems. Both block, and collapsing them would hide the second behind the first permanently |
| **No verifier can satisfy a human condition** | `verification._find` + `validate_compliance_capabilities.py` + `test_compliance.py` | Probed on every source: a `HUMAN_CONFIRMATION` condition must resolve `UNKNOWN` whatever the arguments. A program that could decide one would be the system granting itself permission |
| **A capability is checked, not merely registered** | `capability_failures` conformance checks, asserted per source | Each check runs the real gate against the real configuration, asserts every denial the evidence names, **and asserts its own control case passes** — a filter that denies everything would otherwise satisfy every denial assertion |
| **Every condition resolves to a real verifier** | `validate_compliance_capabilities.py` (zero dependency) | A condition naming a capability nobody built is `UNKNOWN`, and the validator fails rather than letting it sit unnoticed. Also fails on a registered capability no condition names (§5: no unused abstractions) |
| **An exact required notice is traceable to its evidence** | Same script | The FRED sentence must appear in the review evidence that prescribed it. A notice nobody can trace to a document is our wording, not the source's |
| **Attribution cannot be silently omitted** | `render_attribution` raises; `AttributedArtifact.derive` cannot drop an obligation; `test_compliance.py` | A notice missing half its obligation looks like attribution and is not, and the loss would happen at whichever transformation forgot to copy it |
| **Unknown resource scope fails closed** | `authorize_resource`; six rule kinds, all denying | An unrecorded licence, an unstated geography, unread series notes and `UNKNOWN` content origin are all refused. An unexamined resource is not one known to be covered |
| **A source-level approval cannot override a dataset exclusion** | Same, plus `test_compliance.py` | World Bank passes the gate; the Microdata Library still does not |
| **No credential value reaches a log, a response or an exception** | `CredentialStatus` has no field for one; `source_condition_verifications_no_secret_value_check`; sentinel test | Structural rather than conventional: leaking it would require going and reading the environment, which is a visible change |
| **No credential is present in CI, and none is in `.env.example`** | `ci.yml` | A source that became runnable because a build secret was added would be one nobody decided to make runnable |
| **An ineligible source produces no authorization** | `build_authorization` raises; asserted for all 13 sources in two places | The §27 property. Not a flag the collector checks — the absence of the object it needs |
| **Python and SQL agree with conditions verified on both sides** | `test_compliance.py`, `test_source_review.py`, `conftest.recorded_satisfied_keys` | The two implementations are compared on the *same inputs*. Satisfaction is environment state, so a Python gate evaluated without it would report a divergence that is really a missing argument |
| **Eligible is not enabled, and neither is implemented** | `sros-source enable` refuses; `IMPLEMENTED_COLLECTORS` is empty; `assert_registry_grants_nothing.py` | Three facts. A switch ahead of the thing it switches reads as "this is running" |
| **The planner does not dispatch a job nothing can run** | `acquisition_block(report, implemented_collectors)`, fail-closed default | Found by making sources eligible: the planner would have emitted `acquire.collect` with no collector behind it. The two acquisition gates are named separately because different work clears them |
| **CI verifies rather than trusting recorded state** | `sros-source verify --apply` in the integration job | A capability removed after verification would leave a stale `satisfied` true. Re-verification takes a source out of eligibility as readily as into it |

### Gates added in Mission 1.5

The first collector exists, so three Mission 1.0-1.4 guards were **narrowed**
rather than deleted -- the same discipline applied to the D-03 guard in 1.2 and
the enablement guard in 1.4. A guard that becomes false stops protecting
anything; a guard that names its boundary keeps working after the boundary
moves.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A collector cannot run without an authorization** | `collect`'s signature; `test_collector_conformance.py` | Structural, not behavioural: the context is the first positional parameter with no default, so nobody can add an overload that omits it. Mission 1.4's recorded debt, paid |
| **The collector cannot build its own authorization** | Module-namespace assertion | `build_authorization`, `load_catalog` and `load_compliance` are not importable names in the collector module. A collector that could authorise itself could approve itself |
| **A refused resource costs zero network calls** | `RecordingTransport` call count | Not "is refused" -- **zero calls**. A gate that refuses after the request went out has prevented nothing |
| **No public signature accepts a URL** | Parameter-name scan over `collection.__all__` | The shape an escape hatch takes when someone adds one "just for testing". `host_of` is exempted by name, with the reason recorded |
| **A path cannot be a URL, and cannot traverse** | `HttpRequest.__post_init__` | The transport takes a path. Handing it an absolute URL is a construction error |
| **An indicator cannot reshape the request** | `WorldBankRequest.__post_init__` | It becomes a path segment; a slash or a query character would change what is fetched |
| **An unauthorized host is refused at the transport** | `HttpxTransport._compose` | Checked at the last place before a socket as well as at the collector: a guard that exists only further up is one a future caller routes around |
| **Redirects are not followed** | `follow_redirects=False`, and a 3xx is an error | A redirect is the documented way out of a host allowlist |
| **Only one file may reach a network** | `ci.yml`, `test_collector_conformance.py` | Mission 1.0's blanket ban, narrowed to `collection/transport.py`. Naming where the network IS says more than asserting it is absent |
| **Collectors live only in the collection package** | `ci.yml`, both suites | The registry and compliance packages decide whether collection may happen. A collector inside either would put the decision and its execution in one place |
| **The switch never gets ahead of an implementation** | `sros-source enable`; `IMPLEMENTED_COLLECTORS` | Eurostat is eligible and has no collector, and cannot be enabled. Found the hard way: a Mission 1.4 test enabled a real collector as a side effect the moment World Bank gained one |
| **Nothing is collected from a source with no collector** | Both suites, asserted as a set relation | Replaces `raw_records == 0`, which was true of every mission until one collected and then stopped being a property |
| **Retention cannot be chosen by a collector** | `build_draft` has no expiry parameter | Enforced by construction: there is nothing to pass |
| **Attribution cannot be composed by a collector** | Same -- no attribution parameter | It is rendered from the obligation the review recorded, and rendering fails closed |
| **The fingerprint ignores retrieval time** | `test_world_bank_collector.py` | Hashing it would make every retrieval a revision, which is how an idempotent collector grows a table forever |
| **Pagination cannot loop** | Bounded `range`; page-advance check | A source repeating page 1 is reported as a fault rather than absorbed until a limit hides it |
| **A deterministic 4xx is never retried** | `_status_failure` + `RETRYABLE_CODES` | One call, not three. Repeating a rejection is how a rate limit becomes a ban |
| **No response body reaches a job result** | `AcquisitionFailure`; sentinel test | §33. A driver has no obligation to keep secrets out of its own messages |
| **Duplicate delivery writes no second row** | Shared-connection job test | At-least-once delivery honoured without claiming exactly-once |
| **Raw records are tenant-isolated** | Two workspaces, RLS, `test_world_bank_collector.py` | A worker cannot write into another workspace, and a query with no tenant filter still returns only its own |
| **The live suite is opt-in and absent from CI** | `SROS_ENABLE_WORLD_BANK_SMOKE_TESTS`, `ci.yml` | A suite that quietly became enabled would show up as traffic to somebody else's servers rather than as a red build |

### Normalization (Mission 1.6)

The first stage that reads what a collector wrote. Its guards protect a
different property from collection's: not *may we fetch this*, but *did the
transformation invent anything*.

`validate_normalization.py` is zero-dependency and was **probed against fourteen
deliberate violations before being believed** — the same discipline the gitleaks
configuration needed, and for the same reason: a validator that has only ever
run against clean code is a validator whose patterns have never been exercised.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Normalization reaches no network** | `validate_normalization.py` parses every import in the package | Not a grep for `httpx`: an AST walk, so `from urllib.request import urlopen` and `import socket` are caught too |
| **Not even the sanctioned transport** | Same, on relative imports | The blanket ban would be satisfied by importing `collection/transport.py`, the one file allowed to hold a client. Reaching the network through the door left open for a collector is still reaching the network |
| **No LLM and no embedding library** | Same | Normalization is deterministic and reproducible. A model deciding a geography would make it neither, and D-12 is still open |
| **No signal, claim or evidence table** | Same, on SQL string literals | A mention in prose is how the rule gets explained; a mention inside a query is the thing forbidden |
| **The vocabulary matches the contract** | Same, against `domain.v1.json` and migration 0009 | Seven closed enums and one registry. A vocabulary living only in Python drifts from the schema `CHECK` and the TypeScript side at once |
| **Record kinds in code match the ones seeded** | Same | Two hand-maintained copies of one fact drift, and the drift is found by whoever trusted the wrong one |
| **Every geography entry records its basis** | Same, over `geography-mapping-v1.json` | A classification that cannot be re-verified is indistinguishable from a guess |
| **No aggregate carries a country code** | Same, plus `CanonicalGeography.__post_init__` | The "World is a country" error, refused at the data and at the constructor |
| **Attribution cannot be dropped** | `build_normalized` has no attribution parameter; signature test | Structural. A behavioural test would pass equally well against a builder with an `attribution=None` nobody had used yet |
| **Retention cannot be chosen** | Same — no expiry parameter | The window is the resolved normalized tier, anchored on normalization, and the raw expiry is deliberately not copied |
| **Missing is never zero** | `CanonicalValue.__post_init__` | Constructing a `NOT_REPORTED` value carrying a number raises. That constructor is where the bug would have to pass |
| **Floats are refused as input** | `decimal_from` | A value that has been through IEEE-754 may already differ from the source's; re-reading it would bake that in |
| **Re-running writes nothing** | Identity unique constraint; job test; the real six records | Idempotency without claiming exactly-once delivery, which Celery does not provide |
| **Output cannot change without a version bump** | `NON_DETERMINISTIC_OUTPUT` on an identity collision with different content | Overwriting would destroy the stored representation; the version *is* the identity that would distinguish them |
| **A revision does not overwrite its predecessor** | `superseded_at`, scoped to one lineage | Crossing lineages would make writing schema 2 retire schema 1 — the selection policy D-08 forbids inventing |
| **A cross-tenant reference cannot be written** | Composite FK on `(workspace_id, raw_record_id)` | Layer three. RLS and the repository filter can be forgotten; a structural impossibility cannot |
| **The planner does not dispatch normalization for a source with no normalizer** | `normalization_block(report, collectors, normalizers)`, fail-closed default | The gap Mission 1.5 opened: the old reason said "no collector is implemented", which stopped being true while the capability stayed unavailable |

### Acquisition authorization (Mission 1.9.2)

No new CI job. These are rules inside gates that already run — the source-registry
job and the acquisition suite — and they are listed because each closed a hole
that a passing suite had been reporting as fine.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **An unestablished rights basis is refused** | `authorize_resource`, unconditional rule | It had been checked only inside the licence-allowlist rule, so a descriptor with **no basis at all** passed for every source enumerating no licences — including GDELT, the one source authorised by a direct grant rather than a licence |
| **An unreviewed dataset family is refused** | `allowed_dataset_families` on the scope | `require_dataset_family` refused a resource that could not say what it is, and admitted one that said something nobody had reviewed. A family no reviewer had rejected was indistinguishable from one a reviewer had approved |
| **A job that exceeds the reviewed ceiling is refused** | `AcquisitionBounds.refusals`, via `context.authorize_job_size` | GDELT publishes two files every fifteen minutes since 2019 and its terms limit none of it. The ceiling is the review's; a collector choosing its own would be setting its own permissions |
| **A ceiling with no basis is refused at load time** | `AcquisitionBounds.__post_init__` | A number nobody can re-check survives every later review by looking deliberate |
| **A job that does not state its size is refused** | Same | The asymmetry `ResourceDescriptor` is built on: not saying how much you intend to take is not a size known to fall under a bound |
| **The reviewed path is the endpoint, not the site root** | `endpoint_url` on the access profile, plus `HttpRequest`'s refusal of `..` and of absolute URLs | Fail-closed **by construction** rather than by a new rule: a base of `.../gdeltv3/web/ngrams/` cannot reach `.../gdeltv3/webngrams/`, the sibling dataset this review rejected |
| **Four facts stay four** | `evaluate_readiness`, derived and never stored | Eligible, resource-ready, implemented, enabled. GDELT spent two missions eligible with every resource failing closed, and "eligible" was the most specific word available |

### The second collector (Mission 1.9.3)

No new CI job, and no new queue. What the second collector added are rules inside
the acquisition suite, and they are listed because each one guards a boundary the
first collector never had to cross.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **The reviewed ceiling cannot be redefined in code** | `authorize_job_size` on the context; the string `max_files_per_job` is absent from the collector, asserted | A collector that set its own volume bound would be setting its own permissions |
| **A nine-file job is refused whole** | The check runs once for the request, not per file | Splitting it into two permitted jobs would grant a ceiling the review did not |
| **The route is resolved by LABEL** | `_route` selects `gdelt-web-ngram-files`; `build_raw_record` requires the access label | `access[0]` is GDELT's **deferred** DOC API. Taking it would have authorised the wrong host and recorded `PUBLIC_API` on every file download |
| **Decompression is bounded three ways** | `NgramBounds` — compressed, decompressed, line length | The decompressed ceiling is the one the compressed ceiling cannot give: kilobytes on the wire becoming megabytes |
| **Gzip framing is required** | `zlib.decompressobj(31)` | An HTML error page returned with HTTP 200 fails immediately instead of parsing into plausible rubbish |
| **A truncated stream is not a short file** | `decompressor.eof` checked at the end | Rows already read from an incomplete download are not a complete file |
| **A malformed row discards its file** | Strict four-field parse, fatal | No column shifting: a five-field row is a contract change, and both a change and a wrong file need a person |
| **Our ceilings truncate; the source's contract discards** | `truncated_by_bound` on the file report | The two failures mean opposite things and must not report the same way |
| **Retry cannot duplicate** | `_read_file` returns a list, not a generator | A mid-stream failure would otherwise have already released rows that the retry re-reads |
| **No timezone is invented** | `validate_bucket_label` returns a string; `observed_at` is `None` | H-29 is open, and an assumption stored in a `TIMESTAMPTZ` is the one a reader trusts most |
| **No language code is guessed** | `content_language` stays `NULL` | H-30 is open, and that column is read as a code |
| **CI reaches no GDELT host** | The live suite is opt-in behind `SROS_ENABLE_GDELT_WEB_NGRAM_SMOKE_TESTS` | A developer with a network has not consented to third-party traffic on every run |

### The canonical model gained a second shape (Mission 1.10)

No new CI job. These are rules inside the normalization guard and the model
itself, and each closes a way the model could have been made to lie.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A period cannot claim a zone it does not have** | `CanonicalPeriod.__post_init__`, both directions | `NOT_ESTABLISHED` refuses aware bounds and `ESTABLISHED` refuses naive ones. An aware bound under an unestablished zone carries an offset the source never published |
| **`observed_at` is empty when there is no event time** | `period.event_time`, `None` under `NOT_ESTABLISHED` | A `TIMESTAMPTZ` filled from a wall-clock reading would be an assumption in the column a consumer trusts most |
| **An existing payload cannot change shape** | `timezone_state` serialised only when not `ESTABLISHED` | The payload is inside the content fingerprint; an unconditional key would have reported a revision on every record ever written |
| **A language tag cannot appear without a mapping** | `CanonicalLanguage.__post_init__`, both directions | Resemblance is not a mapping. `ENGLISH` looks like `en`, and the first CLD2 name that does not would be silently wrong |
| **A language cannot be assigned where a geography is expected** | The two value objects share one field name | Asserted structurally rather than by convention |
| **A record kind cannot be declared without being registered** | `validate_normalization.py`, now reading **every** migration | A single filename was right while one kind existed and would have silently stopped covering the second |
| **The term's gram size is never inferred from its text** | Asserted over the payload class's source | A two-word entry in a unigram file is a contract violation, and counting spaces would hide it |
| **A vocabulary entry is not an adapter** | `NORMALIZER_REGISTRY` and `IMPLEMENTED_NORMALIZERS` asserted empty of GDELT | The registry row lets the model describe a shape; it does not claim code exists |

### The second normalizer (Mission 1.10.1)

No new CI job. Rules inside the normalization guard and the adapter itself.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **The adapter reaches no network, model or lookup** | AST walk over its imports | A substring scan fails on the docstring explaining the rule, and teaches the next person to weaken the assertion |
| **No timezone is ever converted** | AST: no `astimezone` / `utcnow` / `now` / `localtime` call, no `tzinfo=` keyword | H-29. The one place a UTC offset could enter the field a consumer trusts most |
| **No language table is embedded** | AST over string constants: `en`, `fr`, `es`, `ko`, `de`, `ja`, `BCP-47` appear nowhere | H-30. A mapping cannot be applied that does not exist |
| **Source text is preserved verbatim** | `_source_text` (unstripped) is separate from `_text` (trimmed) | A term published with an edge space would otherwise be stored as a different term — invisibly, in the payload, the fingerprint and the identity |
| **`gram_size` is never inferred from the term** | Asserted over the mapping code: no `.split(`, no `.count(` | Counting spaces would silently correct a contract violation instead of leaving it visible |
| **A self-contradictory payload is refused** | `gram_kind` checked against `resource_id` | Choosing a winner between two source facts is the silent correction |
| **Quality reasons come out in a stated order** | Built in sequence, never sorted afterwards; asserted over three runs | A consumer branching on the first reason must get the same one every time |
| **An existing payload still hashes to its historical value** | A **literal** sha256, not a round-trip | The assertion that catches `timezone_state` leaking into an `ESTABLISHED` payload and reporting a revision on every record ever written |
| **`only_unnormalized` stays meaningful with two adapters** | One lineage per registered adapter, matched on the collector | Dropping the filter is correct per record and silently wrong in bulk: a workspace larger than the batch bound would re-read its first page forever |

### The Signal model (Mission 1.11)

No new CI job. Rules in the schema validator, in the constructor, and in the
database itself -- and where a rule could live in either, it lives in both.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A dropped constraint is not compared against the contract** | `validate_schema.py` strips `DROP CONSTRAINT` definitions before checking | Two live cases pair a drop with a rename, so a value set that was deliberately changed read as drift and the check reported a failure that was not one |
| **A renamed column is checked under its current name** | `validate_schema.py` applies `RENAME COLUMN` to the folded table body | Without it, the retention check asserted `collected_at TIMESTAMPTZ NOT NULL` on a table whose column is `derived_at` -- and passed, while measuring nothing |
| **Nine closed-enum sites across two signal tables** | `validate_schema.py` compares each `CHECK` against `domain.v1.json` | Each of these decides how a derived signal is READ: a family, a direction, a magnitude kind, a temporal basis |
| **No GDELT signal can carry an event time** | `CHECK (observed_at IS NULL OR temporal_basis = 'COMPARABLE_INSTANTS')` | H-29. The normalizer refuses to invent a zone; without this the layer above could invent one back |
| **No signal can claim a direction without an order** | `CHECK (direction = 'NOT_APPLICABLE' OR temporal_basis IN (...))` | H-32. "Increasing" is a statement about before and after |
| **The basis cannot disagree with its own window** | `CHECK (temporal_basis = temporal_window ->> 'basis')` | Two answers to one question is how the wrong one wins |
| **A deterministic signal carries no model provenance** | `CHECK` pairing `derivation_kind` with `model_version` | Mission 1.11 §23 as a constraint rather than a sentence |
| **A magnitude is exact and unbounded** | `NUMERIC`, replacing `DOUBLE PRECISION CHECK (BETWEEN 0 AND 1)` | The old column could not hold a change from 55 to 81, and a float gives back at the first subtraction what the normalization layer exists to guarantee |
| **A ratio or a count names no unit** | `CHECK` on `magnitude_kind` against `magnitude_unit_state` | GDELT publishes four columns and none is a unit |
| **A signal cannot reference another workspace's records** | Composite FKs on `signal_inputs` and on `evidence.signal_id` | The second was a pre-existing gap: migration 0005 made `claim_id` composite and left `signal_id` behind |
| **One derivation is one row** | `UNIQUE (workspace_id, derivation_fingerprint)` plus a UUIDv5 id over the same material | Two rows for one derivation are indistinguishable from two independent findings, which is the one shape evidence aggregation must never be handed |
| **A registered signal type resolves on an empty database** | The two entries are written by migration 0012, not by a seed | `demand_signal_type` had no migration-written entry, so `nlp.signals` accepted an insert on a seeded machine and rejected it everywhere else |
| **Thirteen constraints verified by the constraint that refused** | A rollback-only probe asserting `exc.diag.constraint_name` | Its first version asserted "some error was raised" and every case passed while the real cause was a column the fixture forgot |

### The first signal extractors (Mission 1.11.1)

One new CI step, in the existing normalization-boundary job.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Derivation reaches no network, model or embedder** | `validate_signals.py`, walking every **import** in `sros_nlp` and `sros_signal_model` | The same inputs, parameters and version must produce the same signal, which a model call cannot promise. AST, not grep: a docstring naming a module must not fail the check |
| **`packages/signal-model` contains no extractor** | AST: no class ending `Extractor` | The model says what a Signal IS. An extractor there would make the contract depend on an implementation of itself |
| **No later-stage table is written** | `evidence`, `claims`, `opportunities`, `embedding_provenance` | A Signal is not Evidence, not a Claim and not a Score; each needs something this layer does not have |
| **No extractor names a conclusion** | AST over `extractor_id` constants against a word list | `contrast` and `change` are operations; `trend`, `growth`, `demand` and `attention` are readings, and an id carrying one puts the interpretation in the name |
| **Every declared signal type is migration-registered** | AST over `signal_type_id` against the migrations' INSERTs | The foreign key would resolve only on a seeded database, which is the Mission 1.11 GAP-13 failure one layer up |
| **A refused group carries its reasons** | `CHECK (groups_refused = 0 OR jsonb_array_length(refusals) > 0)` | A count with no reasons behind it is the "something did not happen" the run log replaces |
| **A run's arithmetic adds up** | `CHECK (records_contributed + records_excluded <= records_considered)` | It caught a real defect: contributors were summed per draft, and one record legitimately contributes to several signals |
| **`signal.` does not route to the `nlp` queue** | `TASK_ROUTES`, asserted by name | The `nlp` queue is sized for LLM-backed work; deterministic subtraction would compete for slots meant for something else |

### Temporal order certification (Mission 1.12)

No new CI job. The gates are in the constructor and in the certification's own
shape, because this is the kind of finding that decays quietly.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A certification states its basis** | `TemporalOrderCertification.__post_init__` refuses a blank `basis` | A certification nobody can re-check is a guess with a citation field |
| **A certification covers something** | Refuses an empty `resource_ids` | An entry covering nothing grants nothing; one covering everything is not a finding |
| **Resources are NAMED, never prefixed** | `covers()` tests set membership | The WEB-NGRAM directory publishes an unreviewed `chargram` file per bucket, and a prefix match on `web-ngrams/` would have covered it silently |
| **An observation that cannot name its stream is refused** | `resource_id` defaults to `None` and `covers(None)` is false | Ordering is a property of a publication stream. A default that granted it would be a permission by omission |
| **Ordering never leaks into an instant** | The certification overrides `PERIOD_TIMEZONE_NOT_ESTABLISHED` for `SOURCE_RELATIVE_ORDER` only | H-29. The same record, the same reasons, and the two facts get opposite answers |
| **No certification can name a timezone** | Asserted over the serialised certification: `utc`, `gmt`, `+00:00`, `offset` appear nowhere, and no `timezone` attribute exists | Closing H-32 must not become closing H-29 |
| **A period that could not be represented has no order either** | The override matches `PERIOD_TIMEZONE_NOT_ESTABLISHED` **exactly**, not as a subset | `PERIOD_NOT_SUPPORTED` still withholds ordering |
| **Existing signal identities are unmoved** | Recomputed from stored lineage; `resource_id` is lineage and enters no fingerprint | Adding a field to `ObservationInput` must not silently reissue every signal ever derived |

### The first temporal extractor (Mission 1.12.1)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **No extractor converts a timezone or reads a clock** | `validate_signals.py`, AST over attribute names and `tzinfo=` keywords, scoped to `sros_nlp/extractors` | H-29. This mission gave an extractor datetime arithmetic over unzoned source labels, and one `.astimezone()` would turn a label into an instant silently. Probed against two deliberate violations |
| **Order is asked for, never inferred** | The extractor calls `order_certification(source, resource)` and checks the `label_scheme` before comparing anything | A label that sorts is not a finding. A certification for another scheme would make the 15-minute step wrong silently |
| **A gap is never bridged** | `NON_CONTIGUOUS_SOURCE_BUCKETS`, in the contract and in the `signal_inputs` CHECK | A change computed across a bucket nobody read is indistinguishable from one that happened |
| **An absent term is not a zero** | Two actual observations required; no synthesis anywhere | Zero-filling is the most natural thing to do to sparse lexical data and is wrong in a way nothing downstream can detect |
| **An empty selection is a refusal** | `terms` required; empty raises `PARAMETERS_INCOMPLETE` | "Empty means everything" over a bucket of ~223,000 terms |
| **A dropped constraint is stripped, not its DROP statement** | `validate_schema.py` skips `CONSTRAINT` mentions preceded by `DROP` | With one drop it did not matter. A second migration dropping the same constraint left a superseded value set in the body, which then failed against the contract as drift that did not exist |
| **Group counters may overlap** | Migration 0015 replaced 0013's `derived + refused <= considered` | An extractor pairing within a group derives one pair and refuses another. The counters were right; the constraint encoded an assumption |

### The interpretation boundary (Mission 1.13)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A generated Claim cannot be stored unsupported** | `research.require_evidence_for_generated_claim`, a `DEFERRABLE INITIALLY DEFERRED` constraint trigger (migration 0016), plus `NO_SUPPORTING_SIGNAL` in `build_claim` | The failure the whole layer exists to prevent. Deferred because a claim and its evidence are written in one transaction and neither exists first |
| **`HYPOTHESIS` is exempt by definition, not by exception** | The same trigger, and `requires_evidence` | Requiring evidence for a hypothesis makes the category unusable, which pushes unsupported ideas into `INFERRED` — the exact failure the rule prevents |
| **An interpreter identity is complete or absent** | `num_nonnulls(...) IN (0, 3)` (migration 0017, replacing 0016's spelling) | The obvious spelling evaluates to NULL on a half-filled row, and **a CHECK accepts NULL**. See `testing-strategy.md` §28 |
| **`DETERMINISTIC` implies no model in the path** | `claims_interpretation_provenance_check`, and `ClaimInterpretation.__post_init__` | "Deterministic" is a promise the claim can be regenerated and compared. A model silently voids it |
| **A model is never the evidence** | The evidence requirement applies identically to `MODEL_DERIVED` claims | An LLM proposing a reading is provenance. An LLM as the support is a citation of itself |
| **No chain-of-thought is stored** | No field exists on the draft, the claim or the revision; a test asserts the absence | A private reasoning transcript is not evidence and is not a record anybody can check |
| **Identity survives rewording and never uses an embedding** | `proposition_key` = sha256 over canonical facts (migration 0016 unique per workspace) | D-12 is open. An identity that moved when the model moved would split and merge claims silently |
| **An `OBSERVED` claim may not assert a market reading** | `UNSUPPORTED_INTERPRETATION` in `build_claim`, over a deliberately blunt vocabulary list | The failure that would otherwise ship: arithmetic rewritten as a market fact, weighted by aggregation as a source observation |
| **Evidence names its Claim** | `scoring.evidence.claim_id NOT NULL` (migration 0016) | Evidence for nothing can never be read |
| **One answer per question** | `scoring.evidence.claim_type` dropped (migration 0016); `validate_schema.py` enum-site list updated | Two copies of a claim's type eventually disagree |
| **No generated `NEUTRAL` evidence** | `build_claim`, not a CHECK | A Signal bearing on nothing produces no row. The enum value stays for the human null result a person can own |
| **An absent factor stays absent** | `EvidenceDraft.to_json` omits it; out-of-range is rejected, never clamped | `0.5` and `0.0` are both measurements. `q_i = min(components)` makes the second catastrophic |
| **H-29 / H-30 fail closed at the claim boundary** | `INCOMPATIBLE_TEMPORAL_SEMANTICS`, `INCOMPATIBLE_LANGUAGE_SEMANTICS` | Refusal reasons rather than prose warnings, so a future interpreter cannot proceed by not reading the document |

### The first claim interpreter (Mission 1.13.1)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **No interpreter constructs a non-OBSERVED claim** | `validate_claims.py`, AST over `ClaimType.X` attribute access in `sros_nlp/interpreters` | §5: structurally incapable, not defaulted. A docstring naming INFERRED must not fail it, and a rename must not slip past it. Probed against a deliberate violation |
| **The layer reaches no model, network or embedder** | `validate_claims.py`, walking every import in the interpreters, the job, the repositories and `packages/claim-model` | §39. `MODEL_DERIVED` is unused and an LLM cannot enter the path by accident |
| **`packages/claim-model` holds no template and no SQL** | `validate_claims.py` | The model checks and the interpreter computes. A template in the model would put the proposition where nothing validates it |
| **No template reads a canonical language tag** | `validate_claims.py`, over CALL ARGUMENTS and SUBSCRIPTS | §26, H-30. `ENGLISH` from CLD2 is not BCP-47 `en`, and reading `canonical_tag` would assert a mapping nobody reviewed |
| **No template converts a timezone or reads a clock** | `validate_claims.py`, `.astimezone`/`.now`/`tzinfo=` and four more | §25, H-29. The templates name unzoned bucket labels; one conversion would make one an instant, silently |
| **A template accepts only bases it can phrase** | `_ACCEPTED_BASES`, `INCOMPATIBLE_TEMPORAL_SEMANTICS` | Failing closed. A basis this template does not know is refused rather than described with wording chosen for a different one |
| **The interpretation layer writes no later-stage table** | `validate_claims.py`, over five table names | §41, §43. A Claim precedes an Opportunity; grouping them is a separate decision |
| **Every supported signal type is registered by a migration** | `validate_claims.py` reads `SUPPORTED_SIGNAL_TYPES` from the AST | An interpreter naming a type nothing registered would emit claims about a vocabulary the registry does not hold |
| **The validator itself was probed** | 11 deliberate violations applied to the real files, one per rule | Eleven `ok` lines is what a validator that checks nothing also prints (`testing-strategy.md` §31) |
| **Quoted source data is exempt from the vocabulary guard** | `_QUOTED` stripped before tokenising; three tests use terms `demand`, `market`, `pain` | A GDELT term is arbitrary text. Refusing the most faithful restatement available is the failure the guard exists to prevent (`testing-strategy.md` §30) |
| **Tokens, not substrings** | `_TOKEN` over unquoted prose | `supermarket` is not `market`. A guard with false positives gets loosened until it stops guarding |
| **Claim, revision and evidence land together** | One transaction, plus migration 0016's deferred trigger firing at COMMIT | §20. Evidence in a second transaction is too late by construction, and the trigger says so rather than the reviewer |
| **A key is stored with its preimage** | `claims_proposition_facts_paired_check`, `num_nonnulls(...) IN (0, 2)` | A hash nobody can verify is an identity nobody can dispute (ADR-025) |
| **A considered Signal names its role and its reason** | `claim_interpretation_inputs_role_coherent_check`, every branch NULL-safe | GAP-5. A Signal passed over without a reason is the gap the table closes, reopened |
| **Outcome counters are bounded individually, never summed** | `claim_interpretation_runs_outcome_bounds_check` | The tighter sum is a model of how the counters relate. Migration 0015 had to undo exactly that shape one layer down (`testing-strategy.md` §27) |
| **Reliability is never invented** | Written `NULL`; every record is NON_SCORABLE with MISSING_RELIABILITY | §17, D-03. The seven real claims aggregate to no score, and that is the honest answer rather than a gap to fill |
| **A second execution creates no duplicate** | Proposition-key lookup before every write; proven on the real seven | §28. Two run rows and zero new claims -- idempotent persistence without a claim of exactly-once delivery |
| **A run in one workspace cannot name another's Signal** | Composite FKs plus RLS on both new tables | §35. The read returns nothing AND the run row is refused; both layers asserted |

### Reviewed reliability (Mission 1.14)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Reliability is never a source coefficient** | A five-part scope — source, resource, record kind, claim type, proposition kind — matched in full or not at all | The core rule. `world-bank` alone matches nothing, so a value reviewed for one purpose has no path to another |
| **Policy approval cannot become reliability** | A separate schema, no policy column, and an AST test over string literals excluding docstrings | An APPROVED source does not produce better evidence and a RESTRICTED one does not produce worse. The prose explaining the rule must not fail the check |
| **There is no MODEL_GUESSED origin** | A closed contract enum plus `reliability_assessments_origin_check` | A model may help a reviewer read documentation and may not be the epistemic source. A vocabulary with nowhere to record a guess is what makes that enforceable |
| **A value rests on a retrieved document** | `epistemic.require_documented_basis`, a `DEFERRABLE INITIALLY DEFERRED` trigger | "The publisher is reputable" is a sentence, not a basis. Reviewer reasoning is permitted alongside documents and refused alone |
| **A value states what bounds it** | `reliability_assessments_rationale_check` | A reliability with no stated failure mode is a number nobody can argue with |
| **Human review is not calibration** | `reliability_assessments_calibration_ref_check`, both directions | However careful a review was, it fitted nothing to outcome data. `REFERENCE_PROFILE_V1` stays UNCALIBRATED |
| **Unknown produces no number** | No way to express "unknown" as a value; unknown is the absence of a row | 0.5, 0.8, 1.0 and 0.0 are all measurements. `q_i = min(components)` must never see one that nobody made |
| **At most one current assessment per scope** | `idx_reliability_assessments_current`, a partial unique index | Makes the ambiguous case unreachable through the ordinary path |
| **Ambiguity is refused, never resolved** | `resolve_reliability` refuses independently of the index | Never the closest, never the max, never the mean. A guard that trusts another guard is one schema change away from trusting nothing |
| **Superseded, never updated** | `superseded_at` + `superseded_reason`, `num_nonnulls(...) IN (0, 2)` | An aggregation that used version N must still read version N. Half a supersession is a withdrawal nobody can explain (migration 0017's spelling) |
| **A score's coefficients are reconstructible** | `ReliabilityBinding`: assessment id, key, version, origin, reviewer, review time | Late resolution with a recorded binding, rather than a bare number copied onto a row |
| **No factor implies another** | `resolve_reliability` takes only scope, candidates and supplied — asserted by a signature test | Relevance, directness, extraction confidence and claim confidence are all 1.0 on the real rows and none of them is an argument |
| **The aggregation package still names no source** | The resolver lives in `packages/evidence-reliability`, not in `evidence-aggregation` | The guard that keeps source identity out of the mathematics was left untouched rather than narrowed (`testing-strategy.md` §33) |
| **Assessments are global, with no tenant path** | No `workspace_id`, no RLS policy, `SELECT` only for the runtime role | No tenant data means no leakage path, which is stronger than a correct policy. Asserted by test |
| **A test fixture cannot become a review** | Probes use a resource that does not exist; a test asserts production holds zero assessments | A number in a fixture is indistinguishable from a finding six months later (`testing-strategy.md` §32) |

### The demand-side source round (Mission 1.15)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A verdict change carries retrieved evidence** | `validate_source_registry.py` plus a test per re-reviewed source: URL, finding and retrieval time all required | A verdict that moved on a recollection rather than a document would be indistinguishable from one that moved on evidence |
| **A RESTRICTED verdict names what prohibits it** | A test asserts at least one load-bearing activity is `NOT_PERMITTED` | RESTRICTED must rest on a finding, never on an absence -- which is what `REQUIRES_REVIEW` is for |
| **A failed retrieval changes nothing** | Reddit and Stack Exchange gained no review version, asserted by test | A source nobody could reach is not a source anybody assessed. Recording a version would make an unresolved question look answered |
| **Silence still blocks, with five of six granted** | `ted-eu` records `model_processing` as `NOT_ADDRESSED`; rule 8 blocks the approval | The strongest test the rule has had: a source with an explicit commercial-reuse grant, blocked on one unaddressed activity. Narrowing the assessed use to rescue it is what Mission 1.8 forbids |
| **Technical access is still not permission** | Tests pair a keyless public API with a non-approving verdict, for `hacker-news`, `bluesky` and `ted-eu` | Hacker News publishes an API stating there is no rate limit, and its governing terms prohibit data mining and commercial derivative work. Both facts are true at once |
| **Restricted and prohibited verdicts were not softened** | A test pins the six RESTRICTED and three PROHIBITED sources, and the approving set of five | An expansion round is where a verdict gets quietly relaxed to raise the count of usable sources |
| **Coverage is still not permission** | Both new sources record signal coverage and neither is approving, asserted by test | ADR-017, on the two sources most likely to tempt an exception -- they cover the family with no candidate at all |
| **No collector was built** | Tests assert neither new source is in `IMPLEMENTED_COLLECTORS` or `IMPLEMENTED_NORMALIZERS` | §31. A collector for a `REQUIRES_REVIEW` source is code the gate would refuse to run |
| **CI never contacts a platform** | The whole suite reads the recorded catalog | The review environment could not reach two hosts; a suite that fetched terms would fail on the network rather than on the record (`testing-strategy.md` §34) |

### The TED reuse review (Mission 1.15.1)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A retrieval failure is stored as evidence, not as prose** | `section_reference = "Retrieval failure"` and "empty body" in the finding, both asserted | A citation normally claims somebody read the document. Here it must claim the opposite, and only a structured field does that reliably (`testing-strategy.md` §35) |
| **No search-engine summary becomes evidence** | A test asserts every evidence URL is a first-party EU host | A search returned a summary of the Decision's articles — the one thing in the mission that would have closed the question if treated as evidence |
| **A re-review does not move findings it did not re-establish** | `v1.assessments == v2.assessments`, asserted | A mission that set out to close a question and could not is where a finding drifts to look like progress |
| **Five of six granted still does not make six** | Rule 8, asserted against the exact granted/unaddressed sets | TED would be the first transaction-class source and the project wants it. That must have zero effect, and a test is what makes "zero" checkable |
| **ML inference, embeddings and training stay distinct** | `model_processing` is a single named assessment and is never `PERMITTED`; no embedding or training permission is claimed | §3. Collapsing them would let a future embedding use inherit an inference decision the legal text may distinguish |
| **Minimisation and authenticity survive a mission about reuse rights** | Every v1 condition asserted present in v2; personal-data risk and identifier-discard flags pinned | §12, §13. A mission about ML processing is exactly where an unrelated condition gets weakened incidentally |
| **No TED data reached the database** | Live assertions that no RawRecord or NormalizedRecord carries `source_id = 'ted-eu'` | §28. Retrieving legal documents is review work; procurement notices are research data |
| **Zero TED rows, zero assessments, zero opportunities** | Live assertions that hold in EVERY environment, because they follow from there being no TED collector | §27, §30. The counts 12 / 12 / 7 / 7 / 7 are deliberately NOT asserted: they are facts about one database, not invariants, and pinning them failed on the first CI run. "Unchanged" is a property of a run, already asserted by the post-suite digest watcher (`testing-strategy.md` §36) |

### The governing Decision (Mission 1.15.2)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Six granted activities and a blocked source, at once** | A test asserts all six `PERMITTED` *and* `REQUIRES_REVIEW` together | The state most likely to be "tidied up" by someone who sees six greens and assumes the verdict lagged. The blocker is not an activity in the matrix -- it is a different body of rights over the same data |
| **A favourable H-34 cannot override an unresolved H-36** | The two are tracked independently and both asserted | §23. The mission's most likely failure was closing the easy question and declaring the source usable |
| **A permission finding rests on the operative text** | The evidence entry must carry the Cellar URL, `Articles 1-13`, "read in full" and the verbatim definition fragment | A summary of a legal instrument must never stand in for it, and a PERMITTED finding is exactly where that shortcut is tempting |
| **ML inference does not authorise model training** | A condition scopes the permission; a test asserts training is named as not authorised | §13. The Decision does not distinguish methods, so a single `PERMITTED` field would otherwise read as authorising everything |
| **Embeddings are not inherited from inference** | A condition names them and D-12; asserted | §14 |
| **Database rights are not inferred from a copyright permission** | H-36 stays in the open questions, and the question records that the Decision was read and searched | An established absence is a different fact from an unknown, and a future reviewer must not re-retrieve what has been read |
| **The EUR-Lex failures stay recorded beside the Cellar success** | Asserted | Otherwise the next reviewer repeats five failed retrievals before finding the route that works |
| **Every evidence URL is first-party** | Asserted against a prefix list; mirrors, archives, caches and GitHub explicitly excluded | §3 |
| **A finding is asserted against its version** | Mission 1.15 and 1.15.1 assertions pinned to v1 and v2; durable properties left on the current review | Seven tests failed when v3 landed. Pinning keeps the append-only history checked instead of relaxing the old assertions away (`testing-strategy.md` §37) |

### The database right (Mission 1.15.3)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A dataset-level licence did not become a database-right grant** | A test asserts that H-36A and H-36B are both open on the review that RECORDS finding `dct:license = COM_REUSE` on the bulk distribution | The mission's central risk. Finding a licence attached to the assembled dataset looks like the answer, and it resolves to the same instrument that says nothing about the right |
| **`appliesTo licence-domain/DATA` is not a grant over a database** | The evidence must record that DATA is a subject class, and that the vocabulary has no DATABASE domain | The single most plausible over-read available in the metadata, and the one a reader in a hurry would make |
| **CC BY 4.0 on `ted-csv` does not licence `ted-1`** | A condition names both datasets and says so; tests assert the condition and assert the overlapping-coverage inconsistency is recorded | CC BY 4.0 §4 *does* grant extraction of a substantial portion. Carrying it across from a DG GROW CSV subset to the XML corpus would be choosing a licence by choosing a filename |
| **The favourable fact is recorded in full before being refused** | Tests assert the CC BY finding, its §4 wording, AND the inconsistency in the same evidence entry | A refusal that omits the fact it refuses reads as if the fact was never found |
| **CC0 stays scoped to SIMAP system metadata** | Asserted against the re-read legal notice; the undefined scope became a question in the request rather than a finding | §6. Reading "system metadata" onto the notice corpus would waive the right over exactly the fields the engine wants, which is why it is the reading to distrust |
| **H-36A and H-36B are tracked separately** | Two open questions, each asserted for its own vocabulary — *maker* and *substantial investment* for subsistence, *not addressed* for grant | §10. Subsistence and grant have different answers and different addressees; collapsing them loses which one is open |
| **Package sizes recorded without downloading a package** | The evidence must say HEAD and "no package body was downloaded"; the byte count is asserted | §4. The line between metadata and research data had to be visibly found rather than quietly crossed |
| **A correction to an earlier mission is visible** | The API scroll-mode limit is asserted present in the evidence, and the superseded reasoning is banner-marked in the 1.15.2 document | Mission 1.15.2 reasoned the API was less exposed than bulk. Silently absorbing the correction would leave a wrong sentence authoritative |
| **General legislation is not source policy evidence** | A test asserts Directive 96/9/EC appears in NO registry evidence row | It belongs in the legal packet. Putting it in the registry would be turning general legal knowledge into project evidence |
| **Nothing claims to have been sent** | Tests assert the request says "prepared, not sent", carries an operator-send status, and that no `sent_at` exists anywhere in the catalog | §21. A repository that can draft a message must never imply it delivered one |
| **The packet offers no legal conclusion, and records the unfavourable outcome** | Both asserted | §22. A packet that only describes the outcome we want is advocacy, not a question |
| **No TED module exists in the acquisition package** | The file tree is walked for any module whose stem contains `ted` | §28. "No collector" checked against the tree, not only against a registry a new module could forget to join |

### The local private research route (Mission 1.15.4)

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **No summary can become operator evidence** | Asserted that NO source in the catalog carries an `OPERATOR_CORRESPONDENCE` evidence row, at any review version | §32. A user transcription describing a Publications Office reply exists outside the repository. A tripwire, not a validator: the first real response is a visible diff (`testing-strategy.md` §40) |
| **Local use creates no permission** | The verdict is asserted unchanged after a review that narrowed the use case; the review names the four forbidden conclusions verbatim and refuses each | §1, §27. "It is local, therefore anything is allowed" is the failure this whole mission is exposed to |
| **Documented purpose is not a rights grant** | Condition 11 says so; a test asserts the condition contains "not a grant of a database right" and "no route may be authorised on it alone" | §13. Four pieces of enthusiastic operator documentation are exactly what a reader in a hurry would mistake for a licence |
| **The operator's own word "extract" closed nothing** | The Open Data Service invites users to "extract custom datasets across many notices"; the evidence records it AND records that it does not close H-36 | The Directive's verb, used by the operator, in an invitation. Recording it and refusing it is what makes the refusal honest |
| **The gate refuses, and the reason is the gap** | `build_authorization('ted-eu')` is called in a test and must raise with "REQUIRES_REVIEW"; a second test asserts `evaluate_eligibility` has no use-profile parameter | §26, §29. The architectural gap demonstrated rather than asserted |
| **No use-profile concept exists yet** | The contracts and acquisition packages are walked for `use_profile`, `deployment_profile`, `LOCAL_PRIVATE`, `MULTI_TENANT` | If this goes red the proposed extension is being built, which should happen in a mission that says so rather than as a side effect |
| **A local profile cannot migrate to a commercial one** | The review states the boundary; the gap document states that an unnamed profile is refused; both asserted | §8. The most likely way this review causes harm later |
| **No compliance configuration for a blocked source** | Asserted that `source-compliance-v1.json` has no `ted-eu` entry | Preparation dressed as permission. The profile is defined in the gap document and authorised nowhere |
| **No SPARQL client anywhere** | The tree is walked for `SPARQLWrapper` and for modules whose stem contains `sparql` | §28. The new route is a query endpoint, so "no collector" needs a second shape of check |
| **The coverage window is recorded, not discovered at runtime** | The evidence must carry "1 march 2023" and "proof of concept" | The Open Data Service holds eForms from March 2023 and a six-form-type slice of Standard Forms. A collector must not learn that from an empty result set |
| **Assessments byte-identical across a route review** | `v4.assessments == v5.assessments` | A review that established no new right must not move a finding it did not re-establish |


---

## 2. Turborepo task graph

Defined in `turbo.json`.

| Task | Depends on | Cached | Notes |
|------|-----------|--------|-------|
| `build` | `^build` | Yes | Excludes test files from the input hash |
| `lint` | `^build` | Yes | |
| `typecheck` | `^build` | Yes | Needs upstream declarations |
| `test` | `build` | Yes | Own package's build, not just upstream |
| `test:unit` | `^build` | Yes | Fast path, no local build |
| `test:e2e` | `build` | **No** | Real browser, real time |
| `dev` | — | No | Persistent |

Caching rules that matter:

- **`test:e2e` is never cached.** An E2E result is a statement about a running
  system at a moment in time, not a pure function of the source.
- **`build` excludes test files from its inputs.** Editing a test must not
  invalidate the build cache.
- **`globalDependencies`** includes `.editorconfig`, `.nvmrc` and
  `packages/typescript-config/base.json` — changing a toolchain-wide file
  correctly busts everything.

### Python and Turborepo

Turborepo does not understand Python imports (ADR-001, Cons). Each Python service
exposes its tasks through a thin `package.json` script layer:

```jsonc
// services/scoring/package.json
{
  "name": "@sros/scoring",
  "scripts": {
    "lint": "ruff check .",
    "typecheck": "mypy --strict src",
    "test": "pytest",
    "build": "python -m build"
  }
}
```

Turborepo hashes the whole service directory rather than a precise import graph,
so Python caching is coarse. It errs toward cache misses, never stale hits.

---

## 3. Lint strategy

### Principles

1. **Lint catches correctness, not style.** Prettier and ruff format own style.
   Overlapping the two produces conflicts that get resolved by disabling rules.
2. **Every rule blocks something real.** A rule that produces noise gets disabled
   in bulk, taking the useful rules with it.
3. **No blanket `eslint-disable` at file scope.** A disable is one line, one
   rule, with a reason.

### TypeScript — rules with specification weight

These are not preferences. Each blocks a specific specification violation.

| Rule | Blocks |
|------|--------|
| `no-restricted-imports` (cross-service paths) | A context importing another's internals instead of its contract (`service-boundaries.md` §4) |
| `no-restricted-syntax` (local domain enums) | The C-02 drift: a domain enum declared outside `packages/contracts` |
| `no-restricted-imports` (LLM provider SDKs) | A business service importing a provider SDK instead of using the LLM Gateway (ADR-006) |
| `@typescript-eslint/switch-exhaustiveness-check` | An unhandled claim type or score family — the conflation §8 forbids |
| `@typescript-eslint/no-floating-promises` | Silently dropped async work; in a pipeline, a lost job is lost evidence |
| `@typescript-eslint/no-explicit-any` | Untyped data crossing a boundary where provenance must be attached |
| `react/no-danger` | Rendering scraped content as HTML |
| `no-restricted-globals` on `process.env` outside config | Environment access scattered through domain code |

### Python — ruff

Enabled rule families: `E`/`W` (pycodestyle), `F` (pyflakes), `I` (isort),
`N` (naming), `UP` (pyupgrade), `B` (bugbear), `ASYNC` (async correctness),
`S` (bandit security), `DTZ` (timezone-aware datetimes), `RET`, `SIM`, `PTH`.

Two of these are load-bearing rather than cosmetic:

- **`ASYNC`** — catches blocking calls inside async handlers. ADR-003 records
  this as the failure mode whose symptom is furthest from its cause.
- **`DTZ`** — forbids naive datetimes. Every observation in this system carries a
  timestamp (`data-principles.md` §9), and recency decay is computed from them.
  A naive datetime is a silent correctness bug in the evidence model. It is also a
  retention bug: `expires_at` is computed from these timestamps
  (`data-retention-policy-v1.md` §6).

### Tenancy and numeric-scale checks

Two classes of bug are severe enough to deserve their own automated checks
(Mission 0.2), because review does not reliably catch either:

| Check | Catches |
|-------|---------|
| Repository/query lint for tenant-scoped tables | A query on a tenant-scoped table with no `workspace_id` filter — a cross-tenant data leak, not a rendering bug (ADR-005) |
| Cache-key and vector-filter enforcement in client wrappers | The two leak paths that do not go through SQL and so never appear in a query audit |
| Contract range validators | A `confidence` outside `[0,1]` or a `*_score` outside `0–100` (`scoring-framework-v1.1.md` §4.1) |
| `MarketScope` shape validators | A `COUNTRY` scope with two countries, an empty list, or an uncanonicalized list — all of which break scope equality and therefore cache and dedup keys (Ontology V2 §4.4) |
| Registry-vs-enum lint | A domain taxonomy declared as a union type or a database enum instead of a registry reference (Ontology V2 §14.3) |

`mypy --strict` is required, not optional: without it Pydantic validates the
edges while the interior stays untyped, and the guarantee ADR-003 was made for
stops at the boundary.

---

## 4. Formatting strategy

| Files | Tool |
|-------|------|
| `.ts .tsx .js .jsx .json .md .yml .yaml` | Prettier |
| `.py` | ruff format |
| Whitespace baseline for everything | `.editorconfig` |

Rules:

- **Formatting is never a review comment.** If a human mentions formatting in a
  review, the automation has failed.
- **CI checks, it does not fix.** `format:check` fails the build; a bot pushing
  format commits makes history unreadable.
- **One formatter per file type.** No exceptions.
- **Markdown is formatted too.** Documentation is production code
  (`PROJECT_MANIFEST.md` §Repository Philosophy).

---

## 5. CI pipeline (planned)

Placeholders in `.github/workflows/`. They are `workflow_dispatch`-only until
Mission 0.2, so they cannot fail on a repository that has no lockfile yet.

```
PR opened
  ├─ changed-paths detection        (avoid running everything on every PR)
  ├─ secret scan                    ALWAYS runs, never path-filtered
  ├─ format:check                   fast fail
  ├─ lint            ─┐
  ├─ typecheck        ├─ parallel
  ├─ test:unit       ─┘
  ├─ contract tests                 schemas still parse the fixtures
  ├─ integration tests              testcontainers: postgres, redis, qdrant
  └─ build

main (post-merge)
  ├─ everything above
  ├─ dependency audit
  └─ image build

nightly
  ├─ E2E (Playwright)
  ├─ full integration suite
  └─ dependency audit
```

### Rules

1. **The secret scan is never path-filtered and never skipped.** It is the one
   gate whose failure is unrecoverable: a leaked credential is compromised the
   moment it is pushed, and reverting the commit does not un-leak it.
2. **Path filtering everywhere else.** ADR-001 accepted "CI must be path-filtered
   or it becomes slow" as a known cost; this is the payment.
3. **E2E is nightly, not per-PR.** Flaky per-PR E2E teaches people to re-run
   failing jobs without reading them, which destroys the value of every other
   gate.
4. **No test in CI touches a live external source.** Recorded fixtures only.
   Otherwise the build depends on a third party's uptime and rate limits, and
   `data-principles.md` §3 gets violated by a CI run.
5. **CI has no production credentials.**

---

## 6. Branch protection (when the remote exists)

- `main` protected, no direct pushes.
- Required status checks: format, lint, typecheck, unit, contract, integration,
  secret scan.
- Required review via `CODEOWNERS` — **D-09 resolved**: the owner is `@Speekyx`
  and `CODEOWNERS` is updated accordingly. Note for any future change: GitHub
  does not error on an unresolvable owner. It silently assigns no reviewer, so
  branch protection would appear configured while enforcing nothing.
- Linear history, no merge commits from feature branches.
- Conversation resolution required.

---

## 7. What automation cannot check

These stay in human review, and they are the ones that matter most in this
system:

| Check | Why a machine cannot do it |
|-------|---------------------------|
| Is this claim correctly typed as `OBSERVED` vs `INFERRED`? | Requires knowing what the data actually supports |
| Is this confidence value justified? | Requires judgment about the evidence |
| Does this contradict an authoritative specification? | Requires reading both |
| Is this LLM prompt injection-safe? | Requires adversarial thinking |
| Is this source's usage lawful? | Requires reading terms of service |
| Is the evidence aggregation sound? | Requires domain reasoning |
| Is this retention period justified by the source terms? | Requires reading the terms and recording a `basis` (`data-retention-policy-v1.md` §3) |
| Is this job genuinely idempotent? | Requires reasoning about at-least-once delivery (ADR-004) |
| Are these two discoveries the same opportunity? | Identity resolution is an analytical judgment, not a unique constraint (Ontology V2 §12.3) |
| Should this taxonomy value be a new registry entry or an alias of an existing one? | Requires domain judgment |

The PR template (`.github/PULL_REQUEST_TEMPLATE.md`) asks about these explicitly,
because a checklist item is the cheapest available prompt to think about them.
