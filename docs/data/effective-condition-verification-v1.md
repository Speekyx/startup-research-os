# Effective Condition Verification V1

**Authoritative.** Mission 1.15.6.2. How a persisted human decision and a live
machine verification combine into the state the authorization gate reads.

**One sentence:** a condition is answered by whatever can actually answer it —
a capability by running it now, a judgement by reading what a person recorded —
and **a machine that cannot answer never counts as a no**.

---

## 1. The problem this exists to solve

Mission 1.15.6.1 recorded the first real `HUMAN_CONFIRMATION` in this repository
and found two defects the moment it existed.

**The two halves never met.** `verify_source` answers every condition the same
way: by running a verifier now. That is right for a capability and impossible
for a judgement — an operator's acceptance of a legal risk is not observable at
any moment, so the verifier answered `UNKNOWN` and would answer `UNKNOWN`
forever. Meanwhile the decision sat in the database. `build_authorization`
consulted only the live side and refused a source whose conditions were, in
fact, all satisfied.

**And re-verification revoked decisions nobody withdrew.** `verify --apply`
persisted that `UNKNOWN` like any other non-`SATISFIED` result, which wrote
`satisfied = FALSE` over a recorded acceptance. Mission 1.15.6.1 shipped with an
operational warning attached: *do not run `verify --apply` for TED*.

Both come from the same missing distinction: **absence of a human answer is not
a negative human answer.**

## 2. The two kinds of condition

| | `HUMAN_CONFIRMATION` | `CAPABILITY` · `ACCESS_METHOD` · `CONFIG_REFERENCE` |
|---|---|---|
| What it asserts | a person decided something | a mechanism holds right now |
| Observable by a program | **no, ever** | yes, cheaply |
| Answered from | **persistence** | **live evaluation, every time** |
| Changed by | another explicit human decision | the world changing |

**A `HUMAN_CONFIRMATION` is not a sensor.** No pass over the configuration can
observe *the operator still accepts this*, because that is not a property of the
configuration. Asking is not merely useless; persisting the non-answer is
destructive.

**A machine condition is not a memory.** A capability recorded satisfied months
ago says what was true then. Re-running it is the entire point of a mechanical
check, and reading a stale copy instead would be the persist-everything failure
this separation exists to avoid.

## 3. The effective verification set

`resolve_effective_verifications(source, use_profile_id, config, decisions, environ, now)`

For every condition the current review requires:

```text
HUMAN_CONFIRMATION  ->  a usable persisted decision, if one exists
                        otherwise the placeholder, which is UNKNOWN, which blocks

everything else     ->  the verifier, run now
```

**Nothing is source-specific.** A source with no human condition resolves
exactly as `verify_source` does, decisions supplied or not.

### 3.1 Which persisted decisions are usable

A supplied record is used **only** when every one of these holds. Each rejection
is fail-closed and answers a different way a wrong record could arrive:

| Requirement | Why |
|---|---|
| `verification` is `HUMAN_CONFIRMATION` | **a supplied record can never satisfy a machine condition.** This is what stops the parameter from becoming a way past the gate |
| authored by a person, not the placeholder | `human-confirmation` is the verifier name the dispatcher writes when it *cannot decide*. It is not an actor and its records are not decisions |
| same `source_id` | a decision about one source never speaks for another |
| same `review_version` | an acceptance belongs to the review it was made about (§5) |
| result is `SATISFIED` | a recorded **withdrawal** is a decision too, and it must leave the condition unsatisfied |
| the condition is required by this review | a decision about something this review does not ask is not an answer to what it does |

Where a person recorded the same decision more than once, **the most recent
wins**. History is append-only; the current answer is the latest one.

### 3.2 What a caller supplies, and why it is not a bypass

`build_authorization(source, profile, config, decisions=…)` takes the persisted
decisions. It does **not** take a merged verification set: the resolver does the
merging, under the rules above.

**The compliance layer never opens a database, and must not.** ADR-009 requires
the registry model, the compliance layer and every zero-dependency validator to
run with nothing installed — `validate_compliance_capabilities.py` depends on
it. So the persisted half is *injected*, read by
`read_human_decisions(conn, source_id, use_profile_id, review_version)`, which
applies the same filters again in SQL.

**Empty is the safe default.** A caller with no database supplies nothing, every
human condition resolves `UNKNOWN`, and the gate refuses — which is what every
caller did before this parameter existed.

### 3.3 Safe for a gate is not safe for a report (amended in Mission 1.15.6.3)

The sentence above is true of the **gate** and was read as though it were true
of everything. It is not, and the difference is what a refusal means in each
place.

**A gate that refuses without asking is conservative.** Nothing is collected
that should not have been; the worst outcome is work not done.

**A report that refuses without asking is wrong.** It tells an operator that the
decision they recorded does not exist, names the one condition they answered as
the reason the source is blocked, and does it in the command
`source-review-guide.md` §9 tells them to run. Nobody is protected by that, and
the reader stops looking.

So the rule for every caller that evaluates readiness, eligibility or
authorization for a human to read:

> **Pass the decisions, or state why there are none.** `decisions=()` is a claim
> about a deployment — *this one holds no operator decision* — and a caller that
> has not read them is not entitled to make it.

`evaluate_readiness(source, profile, config)` type-checks, runs, and asserts an
absence it never checked. Three CLI call sites did exactly that, so `readiness`
and the footers of `show` and `authorization` disagreed with the gate printed
beside them. The commands now read once per source through
`_recorded_decisions` — the one sanctioned reader, which wraps
`read_human_decisions` and degrades with a note rather than a traceback — and
pass that set to every consultation they make about that source.

**A source with no `HUMAN_CONFIRMATION` condition never opens a connection**,
which is what keeps the reports documented to run without a database running
without one.

## 4. `verify --apply` no longer revokes

`record_verifications` **skips** any record that is the human placeholder. No
row is written and no boolean is touched.

```text
sros-source --use-profile local-private-research-v1 verify ted-eu --apply

  ted-attribution                                SATISFIED   recorded
  ted-official-route-only                        SATISFIED   recorded
  ted-personal-data-minimisation                 SATISFIED   recorded
  ted-database-right-residual-exposure-accepted  UNKNOWN     UNTOUCHED
```

Two properties, and the second is easy to miss:

- **the boolean survives**, because nothing wrote to it;
- **no row is appended**, because a log that gained an `UNKNOWN` entry every
  time somebody ran the verifiers would bury the one decision that matters under
  a history of machines shrugging.

The command says so out loud. Silence here used to mean *revoked*, and an
operator had no way to tell.

## 5. Review and profile scoping

Unchanged from Mission 1.15.6.1, and now enforced in three places rather than
one: the SQL read, the resolver's filters, and the database's own structure.

- **Profile.** A verification row hangs off a condition, the condition hangs off
  exactly one review, and that review names exactly one `assessed_use_profile`.
- **Review version.** Each review version owns its own condition rows
  (`registry.source_review_conditions` is keyed `(review_id, condition_key)`).

So TED's acceptance on local review **v2** cannot satisfy a future v3, the
commercial profile, another source or another condition. **A materially changed
review requires a new decision**, which is the point of versioning a review.

### Superseded reviews

A decision attached to a superseded review **remains as historical evidence and
satisfies nothing current**. It is not deleted, not migrated and not
reinterpreted. If a new review carries a `HUMAN_CONFIRMATION` condition, a
person decides again.

## 6. Withdrawal

**A human decision is changed by another human decision, never by a machine
run.**

The mechanism already exists and needed no extension: a person writes a row
under their own identifier with a result other than `SATISFIED`. Because that
record *is* human-authored, `record_verifications` processes it normally and
clears the boolean, and `resolve_effective_verifications` stops finding a usable
decision — so the condition returns to `UNKNOWN` and the gate refuses.

**No CLI verb writes one**, for the reason Mission 1.15.6 recorded: a command
that records human confirmations is one flag away from a script that records
them.

**Open, and deliberately not built here:** there is no operator workflow for
withdrawal — no prompt, no audit trail beyond the row, no notification that an
authorization has lapsed. Building one is a mission of its own. What matters is
that the *semantics* exist and nothing else can reach them.

## 7. What the SQL view means

`registry.source_eligibility` reads `registry.source_review_conditions.satisfied`
for every condition, so it reports the **last recorded** state:

| Condition kind | What the view shows |
|---|---|
| `HUMAN_CONFIRMATION` | the decision — current, since only a person changes it |
| machine kinds | the result of the **last `verify --apply`**, which may be old |

**The view alone does not prove runtime authorization**, and this document is
where that is said rather than assumed. It is the right input for a database
trigger — `require_eligibility_for_collector` must be able to refuse an `UPDATE`
without running Python — and it is the wrong thing to read as *this is
collectable now*. The Python gate re-evaluates machine conditions; the view
cannot.

The two agree when the verifiers have been applied recently. When they disagree,
**the Python gate is the stricter and more current answer**, and the view is a
statement about what was last recorded.

No view or schema change was needed. The distinction is in what each is *for*.

## 8. What did not change

- **`verify_source` did not learn to evaluate human intent.** It still answers
  `UNKNOWN` for a `HUMAN_CONFIRMATION`, unconditionally, and no verifier in this
  repository writes one. The correction happens where the state is composed, not
  inside a verifier.
- **`HUMAN_CONFIRMATION` was not reclassified.** Turning a judgement into a
  capability would be the reword `source-review-guide.md` §9 forbids.
- **No machine verifier can satisfy or revoke a human condition.**
- **No persisted machine state authorises anything.**
- **No source policy conclusion moved.** Sources with no human condition behave
  exactly as before.
