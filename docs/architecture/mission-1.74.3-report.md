# Mission 1.74.3 — The first outward act in this arc, and it was the operator's

**Outcome: `R1_SENT_OPERATOR_ATTESTED_BYTE_VERIFICATION_NOT_REACHED`.** The operator
posted the R1 issue once, manually, and attested to it. The execution record moved to
`SENT`. **This repository created nothing, invoked no `gh`, and made no GitHub API
call.**

---

## 0. What happened

| | |
|---|---|
| issue | `https://github.com/jsdelivr/globalping/issues/907` |
| repository | `jsdelivr/globalping` — matches the approved target |
| author | `Speekyx` — matches the approved identity |
| posts | **1**, against a maximum of 1 |
| status | `SENT` |
| attestation level | **`OPERATOR_ATTESTED`** |
| approval digest | `bcddd2b8…`, **unchanged** |

## 1. The supplied issue number was a placeholder, and no number was invented

The attestation read `issue_number: XXXX` — the template line, unfilled. A number was
**not** invented. The URL already carries it, so `907` is **derived from the URL** and
recorded as such: the two are the same fact stated once, not an independent
confirmation. Both the supplied placeholder and the derivation are in the record, and
the validator now refuses a number that disagrees with its own URL.

## 2. `BYTE_VERIFIED` was reachable and was not reached, and the reason is Mission 1.63

Mission 1.74.1 established that this channel *can* be byte-verified, because a public
issue has a durable URL. So the obvious move was to fetch it and claim the upgrade.

**The page was fetched, and the upgrade was refused anyway.** The retrieval went through
an HTML-to-markdown conversion **and a summarising model**, and Mission 1.63 established
that **a retrieval summary is not a document** where a sentence decides a gate. The
extraction rendered the body's paragraph break as a space — which is an artifact of the
conversion rather than evidence of a difference, and **precisely because it is an
artifact, that retrieval cannot distinguish it from one.**

So what the fetch bought is recorded as **corroboration** with its limit stated: the
issue exists at the attested URL, it is open, its author is `Speekyx`, its repository and
number match, and **its title matched character for character**. What it does not
establish is byte equality of the body.

`BYTE_VERIFIED` now requires `raw_body_compared` — a raw read of the stored markdown
compared character for character. **That read has not been performed**, and no `gh`
invocation was made.

## 3. A defect in my own R2 gate, surfaced by the first legitimate transition

Mission 1.74.2's gate compared the R1 execution state **live** against a snapshot it took
when it was written:

```python
if r1["execution"]["status"] != scope["r1_execution_state_unchanged"]:
    raise ValidationError("the R1 execution state moved")
```

**That refused the very transition the R1 approval was designed to make.** The first
honest operator attestation turned the R2 gate red — proved by running it against a
mutated copy before changing anything.

The repair is not a loosening. What that gate is entitled to assert is that **Mission
1.74.2** did not move it — history, kept in a field now named
`r1_execution_state_when_this_was_written` — plus that the R1 approval's **binding fields
and digest** are untouched, which it already checked and which is the property that
actually matters. A new check replaces the removed one: R1 may not record more posts than
R1 authorised.

**The value was preserved and only the name and the comparison changed.** A test now
asserts the snapshot still reads `PENDING_MANUAL_OPERATOR_ACTION` while R1 reads `SENT`,
so the two facts are visibly different things.

## 4. The R1 gate got stricter, not looser

A `SENT` record must now name its attester, carry an issue URL on a channel that produces
one, have that URL parse as a GitHub issue URL, have its repository match the approved
target, have its number agree with its own URL, and **state whether the body was compared
raw**. `OPERATOR_ATTESTED` on a channel that can reach higher must say why it stopped
there.

That last one closed a probe escape: deleting `raw_body_compared` slipped through,
because the check only fired for `BYTE_VERIFIED` — so a `SENT` record could leave a
reader unable to tell an unverified send from an unrecorded verification.

## 5. A crashed probe left a record edited, and the gate caught it

The Mission 1.74.2 probe hit an intermittent file lock, its `restore()` raised, and it
left `PROVIDER_CONTACTS: 1` in the R2 approval on disk. **The gate refused it on the next
run**, which is the gate working — and it is Mission 1.67's finding recurring: a restore
that can fail silently leaves a record edited.

The new probe **retries and then proves every file is back**, rather than assuming the
write succeeded. Both affected records were restored from git and the intended change
re-applied.

## 6. What did not move

| | |
|---|---|
| issues created by this repository, `gh` invocations, GitHub API calls | 0 |
| emails sent, mail connector executions, mailbox searches | 0 |
| R2 sends — still `PENDING_MANUAL_OPERATOR_ACTION` | 0 |
| residuals closed, qualification recomputed | 0 |
| Globalping API executions, measurements, target HTTP requests | 0 |
| canonical mutations, Claims, Evidence, scores, model calls | 0 |

Public page retrievals by this repository: **1**, recorded rather than glossed.

**An answer has not arrived.** The issue is open; R1's verdict is unchanged at
`R1_PARTIAL_IMPLEMENTATION_ONLY`, the tally is still 10 PASS / 2 PARTIAL / 0 FAIL, and
`COUNTERPART_UNRESOLVED` stands. **A sent question is still not an answer.**

## 7. Verification

- Both gates probed with **42 deliberate violations, 42 caught** — 39 by rule, 3 by
  drift — **0 escaped**, plus **4 of 4 positive controls**.
- **One control proves the gate did not simply move its floor**: a properly evidenced
  `BYTE_VERIFIED` record, with `raw_body_compared`, is accepted. Another proves the
  pre-transition `PENDING` state is still representable — a gate that only accepts the
  state we happen to be in is not a gate.
- **One escape found and closed by adding a rule.**
- **Five tests asserted the pre-transition state and were re-pointed rather than
  deleted**, to the property rather than the incidental value. A test asserting an
  execution never happens is a test asserting the approval is never used.
- **2857 bare-python tests**; both runners green; `ruff format --check`, `ruff check` and
  mypy through `uv`; all **46** CI gates.

## 8. Next

- **R2 still waits**: one manual email to `legal@globalping.io`, then an attestation. Its
  ceiling remains `OPERATOR_ATTESTED` and no later mission may claim otherwise.
- **R1 may reach `BYTE_VERIFIED`** with a raw read of the issue body compared character
  for character. That needs an explicit instruction; it was not taken here.
- **When the provider replies, freeze the reply verbatim before interpreting it** — the
  provider's words and this project's reading of them must stay distinguishable.

**Mission 1.75 was not started.**
