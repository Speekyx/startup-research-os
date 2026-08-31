# Mission 1.15.6.2 — Effective Verification Set & Human Decision Preservation V1

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.6.2` · **ADR:** none

**Both defects are fixed.** A machine pass no longer revokes an operator
decision, and `build_authorization` obtains the complete verification state
through its normal production path.

```console
$ uv run sros-source --use-profile local-private-research-v1 authorization ted-eu
AUTHORIZATION  ted-eu  (Tenders Electronic Daily (EU public procurement))
  review        v2 APPROVED_WITH_CONDITIONS
  APPROVED ACCESS
    OFFICIAL_API     ted-open-data-sparql
    OFFICIAL_API     ted-search-api
```

No caller merged anything. **No schema migration. No ADR. No contract change.**

---

## 0. The distinction the whole mission rests on

Both defects came from one missing idea: **absence of a human answer is not a
negative human answer.**

`verify_source` answers every condition the same way — by running a verifier now.
That is right for a capability and impossible for a judgement. An operator's
acceptance of a legal risk is not observable at any moment, so the verifier
answered `UNKNOWN`, and `UNKNOWN` was then treated as every other non-`SATISFIED`
result: it blocked the gate, and it was persisted as a cleared boolean.

Naming the two records apart is the entire fix:

| | |
|---|---|
| a **decision** | a person wrote a row under their own identifier |
| the **placeholder** | the dispatcher reporting that no verifier can decide, under the reserved name `human-confirmation` |

Everything below follows from being able to tell those apart.

---

# The §34 questions

## What defect did Mission 1.15.6.1 uncover?

Two. The recorded human decision and the live machine verifiers never met, so
`build_authorization` refused a source whose conditions were all satisfied. And
`verify --apply` was destructive: it turned a recorded acceptance into
`satisfied = FALSE` while the operator had withdrawn nothing.

## Why did recorded human and live machine verification not meet automatically?

Because nothing composed them. `build_authorization` called `verify_source`,
which is entirely live; the decision sat in the database and nothing read it.
Mission 1.15.6.1 could only demonstrate a successful authorization by supplying
the union by hand, and no production caller did that.

## Why was `verify --apply` destructive?

`verify_source` yields `UNKNOWN` for a human condition and `record_verifications`
wrote `satisfied = FALSE` for **any** non-`SATISFIED` result. That is correct for
a capability that stopped holding and wrong for a decision a person made once.

## Did `verify_source` learn to evaluate human intent?

**No, and it must not.** It still returns `UNKNOWN` for a `HUMAN_CONFIRMATION`,
unconditionally. §9 was right: the correction belongs where state is composed,
not inside a verifier. `HUMAN_CONFIRMATION` was not reclassified either — turning
a judgement into a capability is the reword `source-review-guide.md` §9 forbids.

## What is the effective verification set?

What `resolve_effective_verifications(source, profile, config, decisions, …)`
returns: one record per required condition, each resolved from whatever can
actually answer it.

## Which come from persistence, which from live evaluation?

```text
HUMAN_CONFIRMATION  ->  a usable persisted decision, else UNKNOWN (which blocks)
everything else     ->  the verifier, run now
```

## How is precedence decided?

**By the kind of condition, not by a ranking.** There is no contest to resolve:
persistence is the only place a judgement can live, and live evaluation is the
only honest answer for a mechanism. A supplied record is used only when it is
`HUMAN_CONFIRMATION`, human-authored, for this source, for this review version,
`SATISFIED`, and for a condition this review requires. Where a person recorded
the same decision twice, the most recent wins.

## Can live `UNKNOWN` erase a human decision?

**No.** The resolver never consults the live verifier for a condition that has a
usable decision, and `record_verifications` writes nothing at all for a
placeholder record — not a row, not a boolean.

## Can a machine verifier satisfy `HUMAN_CONFIRMATION`? Can it revoke one?

**No to both**, and the second is new. Satisfying was already impossible; revoking
was the defect.

A supplied record cannot smuggle it either: the filters reject the placeholder
whatever result is attached to it, and reject a `CAPABILITY` record for a machine
condition. That last one is tested against a configuration where the capability
**fails** — if supplied records could satisfy machine conditions, that test would
go green.

## How would a human decision eventually be withdrawn?

A person writes a row under their own identifier with a result other than
`SATISFIED`. It is human-authored, so `record_verifications` processes it and
clears the boolean, and the resolver stops finding a usable decision — the
condition returns to `UNKNOWN` and the gate refuses.

**The semantics exist; no workflow was built** (§11). There is no prompt, no
notification that an authorization lapsed, and no CLI verb — for the reason
Mission 1.15.6 recorded. Documented as a future requirement in
`effective-condition-verification-v1.md` §6.

## Is review/profile scoping unchanged? Does a future review inherit? Does the commercial profile?

**Unchanged, no, and no** — now enforced in three places rather than one: the SQL
read filters on review version and profile, the resolver filters again, and each
review version owns its own condition rows. A decision on local v2 satisfies
local v2 and nothing else.

## Are machine capabilities still evaluated live? Can a stale persisted machine verification authorize acquisition?

**Yes, and no.** The resolver's only persistence input is human decisions.
Asserted directly: for a source with no human condition, the resolver's output
matches `verify_source` record for record.

## Does `verify --apply` preserve the TED acceptance? Is it now safe?

**Yes, and yes.** Run against the real database:

```text
recorded: 3 verification(s): 3 satisfied, 0 unsatisfied, 0 unknown;
  1 human condition(s) left untouched
  untouched, and deliberately: ted-database-right-residual-exposure-accepted.
  A machine pass does not answer a human condition, and no longer clears one either
```

The boolean went `True` → `True`, and the log still holds exactly one row for
that condition. **The operational warning in the readiness document is lifted.**

## Does normal `build_authorization` now succeed without a manually supplied union?

**Yes.** `sros-source authorization ted-eu` builds the context. The CLI and the
collection job read decisions with `read_human_decisions` and pass them as
`decisions=`; the resolver composes. A caller supplies *where decisions come
from*, never a merged result.

**Why injected rather than fetched:** the compliance layer must keep running with
nothing installed (ADR-009) — `validate_compliance_capabilities.py` depends on
it. Empty stays the safe default and stays fail-closed.

## What routes appear in the context? Is bulk XML absent?

`ted-open-data-sparql` and `ted-search-api`, preferred route `ted-search-api`.
**`ted-bulk-xml` is absent**, and `authorize_route` refuses it by name.

## Are field restrictions unchanged? Redistribution, training, embeddings?

**All unchanged.** The authorised field set is permitted, every natural-person
field refused alone and hidden among allowed ones, `ted-bulk-xml-daily`,
`ted-bulk-xml-monthly` and `ted-csv-historical` excluded, an unclassified
resource denied. Redistribution `NOT PERMITTED`; training and embeddings `false`
on both registered profiles, D-12 open.

## Are H-36A/H-36B unchanged? Is TED still AUTHORIZATION_READY? Is `resource_ready` still NO?

**NOT ESTABLISHED and NOT ADDRESSED. Yes. Yes.** TED authorises zero concrete
datasets, so a collector holding the context would be refused every resource it
asked for. §22 said to leave that to Mission 1.15.7 and it was left.

## Were any source policy conclusions changed?

**None.** `openalex` is the one worth naming: it has carried a
`HUMAN_CONFIRMATION` condition under the legacy profile since Mission 1.15, and
it is why this had to be generic rather than written around TED. With no decision
recorded it resolves `UNKNOWN` exactly as before, and a decision recorded about
TED does not touch it — asserted.

## Was any collector implemented? Any external data collected? Local research state?

**No, no, and unchanged.** No TED module, client, parser or worker; no network
call of any kind. Research counts before and after: RawRecords 0 ·
NormalizedRecords 0 · Signals 0 · Claims 0 · Evidence 0 · **TED rows 0**. The
`ted-eu` verification log still holds **exactly one** row, with the same actor,
timestamp, reason and wording.

## Is the full suite green? Is the next mission 1.15.7?

**Yes**, and **yes**.

---

## 1. What changed

| | |
|---|---|
| **Contract · schema · migration** | **nothing** |
| `verification.py` | `AWAITING_HUMAN_VERIFIER`; `is_human_decision` / `awaits_human_decision`; `resolve_effective_verifications` |
| `repositories.py` | `read_human_decisions`; `record_verifications` skips placeholders and reports what it left alone |
| `authorization.py` | `build_authorization(…, decisions=…)`, resolving instead of verifying |
| `readiness.py`, `cli.py`, `collection/job.py` | read decisions and pass them |
| Docs | `effective-condition-verification-v1.md` (new); `acquisition-authorization-v1.md`, `source-review-guide.md`, `docs/data/README.md`, readiness, `testing-strategy.md` §50–§51 |
| Tests | `test_effective_verification.py`, plus two inversions |

**No ADR** (§32). The precedence rule is a consequence of what a
`HUMAN_CONFIRMATION` already means — `acquisition-authorization-v1.md` states it
adequately, and ADR-027 and ADR-028 already carry the decisions it rests on.

**No migration** (§31). Mission 1.15.6.1 established the storage is adequate, and
it was: everything needed was already in the log and the join.

## 2. The prediction that came true

`test_reverification_would_clear_the_acceptance` was written in Mission 1.15.6.1
asserting the defect as **current** behaviour, with this in its docstring:

> When a future mission decides how re-verification should treat human
> conditions, this test is where the decision becomes visible: it fails, and is
> inverted rather than deleted.

It failed on the first run of the new code and was inverted. **That is what
asserting a known defect is for**: the fix cannot land quietly, and the test that
proves it is the one that documented the problem.

A second test went red for a better reason — and it is the mission's own lesson
arriving one more time. `test_the_state_and_the_gate_answer_the_same_question`
asserted TED's `list` row ends in `no`. TED is now eligible **on this machine**,
because an operator recorded a decision here. That is deployment state, and
`testing-strategy.md` §49 had already said so a mission earlier. It now asserts
the review the state column reports and leaves the eligibility value alone.

## 3. `except Exception` does not catch `SystemExit`

The CLI helper that reads decisions degrades to "none" when it cannot reach a
database, so the commands documented to run without one keep working. The first
guard was `except Exception` — and `_connect()` raises **`SystemExit`**, which is
a `BaseException`. It did not catch the case it was written for.

The second half was subtler: `psycopg.connect` raises for an unreachable host
*inside* `_connect()`, before the `with` body the `try` wrapped. Two failures,
both landing outside the handler, found by pointing `DATABASE_URL` at a closed
port and at nothing.

Both are handled now, **and the helper says which happened**:

```text
note: operator decisions could not be read (connection timeout expired)
note: operator decisions were not read (DATABASE_URL is not set. …)
```

Returning "no decisions" in silence would be §49's defect again: a guard that
cannot tell *no* from *I could not check*. The refusal is identical either way;
the reader's understanding of it is not.

## 4. What the SQL view means now

`registry.source_eligibility` reads `source_review_conditions.satisfied`, so it
is the **last recorded** state: current for a human decision — only a person
changes one — and as old as the last `verify --apply` for a machine condition.

It is the right input for the trigger that must refuse an `UPDATE` without
running Python, and **it does not on its own prove that acquisition is authorised
now**. Where the two disagree the Python gate is stricter and more current.
Stated in `effective-condition-verification-v1.md` §7 rather than left to be
discovered. **No view change was needed**, because the distinction is in what
each is for.

Today they agree: after `verify --apply`, the view reports TED local with four
conditions and none unsatisfied.

## 5. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | **pass** — 515 tests across 8 packages |
| Pytest suites | **pass** — all 7 packages |
| All seven validators | **pass** |
| Contract generation · generated documents `--check` | current |
| `ruff format` / `ruff check` / `mypy` | **pass** — 141 source files |
| New tests | 31 in `test_effective_verification.py` |
| Superseded assertions | **2 inverted, none deleted** |

## 6. Where this leaves TED

```text
ted-eu + local-private-research-v1 + review v2
  4 of 4 conditions satisfied
    three from the live verifiers, one from a recorded decision
  AcquisitionAuthorizationContext  BUILDS, through the normal path
  AUTHORIZATION_READY

  verify --apply   SAFE
  resource_ready   NO
  H-36A · H-36B    NOT ESTABLISHED · NOT ADDRESSED
  bulk XML         BLOCKED
  commercial       REQUIRES_REVIEW
  collector        NONE
```

**Next: Sprint 1 — Mission 1.15.7, TED Official Search API Collector V1 — Local
Private Research Profile.** Its first act is authorising a concrete resource, and
the verification semantics it needs are now the ones it can rely on twice.
