# Mission 1.15.6.3 — CLI authorization / readiness decision propagation

**Sprint 1. A defect fix, and nothing else.** The operator-facing reports now
answer the same effective verification question the authorization gate answers.

**No policy changed. No governance row was written. No TED data was collected.
No collector exists. H-36A and H-36B are untouched.**

---

## 1. Why the gate and the CLI disagreed

Mission 1.15.6.2 made a `HUMAN_CONFIRMATION` answerable from persistence and
gave `evaluate_readiness` a `decisions` parameter with the signature:

```python
def evaluate_readiness(source, use_profile_id, config, environ=None, now=None,
                       decisions: Sequence[ConditionVerificationRecord] = ()) -> ...
```

**That default is a real state, not a sentinel.** `()` means *this deployment
holds no operator decision*, and the function is right to treat it as one: a
caller with no database must fail closed.

So a call site that omits the argument is not accepting a default — it is
**asserting an absence it never checked**. Three call sites did, and the
assertion is invisible at the call site: the wrong call is shorter than the
right one, type-checks, runs, and returns a plausible answer.

The result, on a deployment holding a recorded acceptance:

```text
sros-source --use-profile local-private-research-v1 eligibility ted-eu
  ted-eu: ELIGIBLE                                    <- the gate, correct

sros-source --use-profile local-private-research-v1 readiness ted-eu
  ted-eu   no   no   no   no   pass the eligibility gate
  blocked: review conditions not satisfied:
    ted-database-right-residual-exposure-accepted     <- the one that WAS satisfied

sros-source --use-profile local-private-research-v1 authorization ted-eu
  AUTHORIZATION  ted-eu ... routes ted-search-api, ted-open-data-sparql
  NEXT STEP: pass the eligibility gate                <- it had just passed it
```

**This is the same shape as the defect Mission 1.15.6 fixed**, one layer over.
There, four reporting commands read the legacy-profile accessor while the gate
beside them used the requested profile. The AST fence added then covered the
modules that *decide*; the modules that *report* were wrong again, for a
different reason, in the same file.

**A gate that refuses without asking is conservative. A report that refuses
without asking is wrong.** The gate's worst outcome is work not done. The
report's is an operator being told the decision they recorded does not exist,
with the condition they answered named as the blocker, in the command
`source-review-guide.md` §9 tells them to run.

## 2. Which call sites failed to pass the persisted decisions

Three, all in `services/acquisition/python/sros_acquisition/cli.py`:

| Command | Site | What it reported |
|---|---|---|
| `show` | the readiness block under `COLLECTOR ELIGIBLE` | `RESOURCE READY`, `NEXT STEP` computed from a readiness that had never seen the decision |
| `authorization` | the footer, after the context was printed | `NEXT STEP: pass the eligibility gate`, below a context built *with* the decision |
| `readiness` | the command itself, single-source and whole-catalog | `elig no`, blocking on the satisfied condition |

`authorization` is the sharpest: it read the decisions, passed them to
`build_authorization`, printed the resulting context — and then built a second,
decision-blind readiness for its own footer.

## 3. Was the defect limited to three sites?

**Three sites needed fixing. The audit covered more, and two findings are
recorded rather than changed.**

Audited: every call to `evaluate_readiness(`, `build_authorization(` and
`read_human_decisions(` in production code, plus every command that prints an
eligibility or readiness verdict.

**Already correct, and unchanged:**

- `_live_eligibility` — reads the decisions itself, so `list`, `eligibility`,
  `show` and `enable` had the right gate verdict all along. That is why the two
  halves of `show`'s own output contradicted each other;
- `collection/job.py` — both `build_authorization` calls pass
  `_recorded_decisions(...)`. The execution path was never affected;
- `validate_compliance_capabilities.py` — supplies records explicitly and must
  never open a database (ADR-009).

**Named, and deliberately not fixed:**

- **`acquisition_cli.py:_context`** builds an authorization for `world-bank`
  with no decisions. Inert today — World Bank's review carries no
  `HUMAN_CONFIRMATION` — and it is a *collection* entry point, not
  operator-facing output. Wiring a decision read into it means choosing a
  workspace and opening a tenant connection before the gate, which is a design
  decision belonging to the mission that needs it, not a keyword argument. It is
  recorded here so it is a known gap rather than a silent one.
- **The gateway API** (`services/gateway/.../api/sources.py`) reports
  `collector_eligible` from the `registry.source_eligibility` SQL view,
  deliberately and by documented design: *running verifiers on an HTTP request
  would make eligibility a property of who asked*. That view reports the last
  **recorded** state, which `effective-condition-verification-v1.md` §7 already
  governs. It is not the Python gate and does not claim to be. Unchanged.

## 4. The canonical decision-reading path, and no duplicated logic

The commands read through **`_recorded_decisions(source, profile)`**, the helper
Mission 1.15.6.2 introduced. It is the only caller of `read_human_decisions` in
the CLI, and:

- returns `()` immediately when the review declares no `HUMAN_CONFIRMATION`, so
  a source that never had one still needs no database;
- catches `SystemExit` **by name** (unset `DATABASE_URL`, missing driver) and
  `Exception` (unreachable host), printing which happened and failing closed.

**No second resolver and no second reader were created.** Verification logic is
untouched: `resolve_effective_verifications` still composes the state,
`read_human_decisions` still applies the profile, review-version, kind and
authorship filters in SQL, and the CLI still contains no SQL of its own. Two
tests assert exactly that — one counts the single `read_human_decisions(` call
site, one refuses the table name anywhere in `cli.py`.

**One signature changed**, `_live_eligibility`, to accept decisions a caller has
already read:

```python
decisions: Sequence[ConditionVerificationRecord] | None = None
```

`None` means *the caller has not read them*; `()` means *the caller read them
and this deployment holds none*. `show` reads once and passes the same set to
the gate and to the readiness beside it, so its two halves cannot disagree and
an unreachable database is reported once rather than once per consultation.

**No TED-specific branching was added anywhere.** The change names no source, no
profile and no condition; a future source carrying a `HUMAN_CONFIRMATION`
benefits without another edit.

## 5. The fence

An omission leaves no token to grep for, so the guard is an AST property:

```python
offenders = [
    f"line {node.lineno}"
    for node in ast.walk(tree)
    if isinstance(node, ast.Call)
    and getattr(node.func, "id", None) == "evaluate_readiness"
    and not any(kw.arg == "decisions" for kw in node.keywords)
]
assert offenders == []
```

It failed with `['line 419', 'line 696', 'line 712']` before the fix, which is
how the three sites were confirmed rather than assumed.

## 6. Tests

`services/acquisition/python/tests/test_cli_readiness_decisions.py`, 25 cases,
**no network and no database**. The persisted half is injected by replacing
`cli._recorded_decisions` — the seam the CLI already uses — so every case
describes a deployment holding an operator decision without depending on whether
the machine running it does (§49).

| Case | Asserts |
|---|---|
| readiness / show / authorization with a decision | eligible, and the satisfied condition is not named as blocking |
| all four commands together | one deployment state, one answer, whichever verb was typed |
| whole-catalog `readiness` | the survey uses the decisions too, not only the single-source path |
| no decision | fail closed, condition named, `authorization` refuses |
| database unreachable | `could not be read`, and still refuses |
| `DATABASE_URL` unset | `were not read`, and still refuses |
| decision on review v1 | does not satisfy v2 |
| decision about another source | does not apply |
| the `human-confirmation` placeholder | is not a decision |
| a recorded withdrawal | leaves the condition unsatisfied |
| a supplied `CAPABILITY` record | contributes nothing |
| a broken route authorization | blocked, with the acceptance intact and the human condition **not** named |
| commercial profile | `REQUIRES_REVIEW`, and the refusal does not mention the condition |
| `world-bank` | unchanged, no human condition, no connection |

The last three of those are the direction that pulls the other way: a persisted
human decision must never make a machine failure pass.

**One existing test was corrected.**
`test_the_acknowledgement_is_stored_verbatim_in_the_row` asserted three phrases
of the operator's French acknowledgement including the newlines that fell inside
two of them. The second deployment recorded the same acknowledgement — character
for character, confirmed by comparison — wrapped at different columns, and the
test failed on a correct row. Whitespace is now collapsed before the comparison.
The phrases are still asserted whole and in order; only the line wrapping, which
belongs to the operator's editor rather than to the decision, is dropped.
Recorded as `testing-strategy.md` §53.

## 7. Answers

| Question | Answer |
|---|---|
| Why did the gate and CLI disagree? | `decisions=()` is a real state, so omitting the argument asserted an absence nobody had checked |
| Which call sites failed to pass decisions? | `cmd_show`, `cmd_authorization` (footer), `cmd_readiness` |
| Was the defect limited to three sites? | Three needed fixing; `acquisition_cli._context` and the gateway view are audited and recorded in §3 |
| What canonical path is now used? | `_recorded_decisions` → `read_human_decisions` → `resolve_effective_verifications` |
| Was verification logic duplicated? | **No.** No new resolver, no new reader, no SQL in the CLI |
| Does `readiness` report TED local v2 correctly? | Yes: `elig yes`, next step *authorise a concrete resource* |
| Does `show` report the same effective state? | Yes: `COLLECTOR ELIGIBLE: yes`, `RESOURCE READY: NO` |
| Does the `authorization` footer name the real blocker? | Yes, and it comes from `next_step` with no source named |
| Does `build_authorization` still succeed? | Yes, unchanged: routes `ted-search-api`, `ted-open-data-sparql` |
| Is `resource_ready` still NO? | **Yes.** TED authorises zero concrete datasets |
| Is the recorded human decision unchanged? | **Yes.** One row, `local-operator` / `acknowledgement-v1` / `SATISFIED`, same timestamp, reference and 1683-character reason |
| Are H-36A / H-36B unchanged? | **Yes.** `NOT ESTABLISHED` and `NOT ADDRESSED` |
| Is bulk still blocked? | **Yes.** `ted-bulk-xml` refused by name and absent from the context |
| Is commercial still `REQUIRES_REVIEW`? | **Yes**, and its refusal does not mention this condition |
| Was any policy changed? | **No.** No review, condition, profile, route, resource or minimisation edit |
| Was any governance row written? | **No.** `verify --apply` was not run in this mission |
| Was any TED data collected? | **No.** No collector, no client, no network call |
| Is the full suite green? | Yes — §8 |
| Is Mission 1.15.7 next? | Yes |

## 8. Validation

| Check | Result |
|---|---|
| zero-dependency suites | 515 tests across 8 packages, pass |
| pytest suites | 1932 across 7 packages, pass |
| seven validators | schema, source registry, compliance capabilities, normalization, signals, claims, evidence aggregation — all OK |
| contract generation `--check` | current |
| catalog render `--check` | matches |
| `ruff format` / `ruff check` | clean |
| `mypy` | no issues in 141 source files |

Also run: environment-template secret check, `assert_registry_grants_nothing`.

**The regression itself, on the real deployment:**

```text
sros-source --use-profile local-private-research-v1 readiness ted-eu
  ted-eu   yes   no   no   no   authorise a concrete resource
  gap: no resource is enumerated for this source

sros-source --use-profile commercial-multi-tenant-research-v1 readiness ted-eu
  ted-eu   no    no   no   no   pass the eligibility gate
```

The second is not a bug. Under the commercial profile the review really is
`REQUIRES_REVIEW`, and the acceptance recorded under the local profile cannot
reach it.

## 9. What did not change

- **No source policy conclusion moved.** Sources with no human condition behave
  exactly as before, and 28 of the 29 have none.
- **`verify_source` still answers `UNKNOWN`** for a `HUMAN_CONFIRMATION`,
  unconditionally. The correction is where state is composed, not inside a
  verifier.
- **No machine verifier can satisfy or revoke a human decision**, and no
  supplied record can satisfy a machine condition.
- **No CLI verb writes a human confirmation**, and none was built.
- **`resource_ready` is still NO**, and no resource was authorised.

## 10. Next

**Sprint 1 — Mission 1.15.7, TED Official Search API Collector V1, local
private research profile.** Its first act is still a governance act: authorising
a concrete resource — the eForms contract notices and contract award notices,
from 1 March 2023, through the reviewed routes — with a stated basis. Nothing in
this mission moved that forward, and nothing in it was supposed to.
