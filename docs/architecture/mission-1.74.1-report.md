# Mission 1.74.1 — One enquiry approved, and nothing posted

**Outcome: `R1_DISPATCH_APPROVED_AWAITING_MANUAL_OPERATOR_ACTION`.** The operator
approved dispatch of **GP-R1-Q1 only**, by a named mechanism, and this repository
performed no outward action.

---

## 0. What the operator approved

| | |
|---|---|
| enquiry | `GP-R1-Q1` |
| mechanism | `OPERATOR_MANUAL_GITHUB_ISSUE` |
| target | `jsdelivr/globalping` |
| identity | `@Speekyx` |
| title | HTTP measurement: is a 3xx response returned without following the redirect? |
| maximum public posts | **1** |

**`GP-R2-Q1` is not approved**, and its packet is byte-identical: still
`send_status: NOT_AUTHORIZED`, still no approval, still unsent.

## 1. The approval is recorded beside the packet, not inside it

Mission 1.66 settled this: marking a frozen document APPROVED changes the bytes that
were approved. Here it would not even have moved the packet's digest — that covers only
the six binding fields — **and it would still have changed the artifact the operator
read.**

So the packet is untouched, and the approval lives in
`globalping-r1-dispatch-approval-v1.json`, which names the packet by a hash **recomputed
from the packet as stored** rather than asserted, plus the packet's own file hash so any
later edit is detectable.

The packet's `send_status: NOT_AUTHORIZED` therefore still reads correctly. That field
means **this document records no authorisation**, and never that no authorisation
exists — the same distinction Mission 1.66 wrote down, now load-bearing for the first
time.

## 2. Every field of the action is pinned, and that differs from the ONYPHE arc

Mission 1.65 stated a cost in advance: the ONYPHE envelope bound a **placeholder**
sender, because under manual email the sender is not determined until the send, so the
hash pinned three fields of four. That cost was then paid in Mission 1.66.1, where the
send matched on recipient, channel and subject and the sender matched nothing.

**It does not recur here.** The destination is a public repository rather than a mailbox,
so mechanism, target, identity and title are all determined before the act, and the
approval digest binds all of them. Changing any one produces a **different approval**
that supersedes this one rather than editing it.

## 3. An approval is not an execution

This is the distinction the gate exists for, and it is unusually easy to lose here:
**once the approval exists, every field an execution record needs is already known.**
Mechanism, target, identity, title and body are all pinned, so a record could fill itself
in completely and be entirely fictional.

| | |
|---|---|
| status | `PENDING_MANUAL_OPERATOR_ACTION` |
| public posts made | 0 |
| issue URL | none |
| issue created by this repository | false |
| `gh issue create` invoked | false |
| GitHub API calls by this repository | 0 |
| operator attestation | none |

`SENT` is reachable only through an explicit operator attestation that the post was made.

## 4. `BYTE_VERIFIED` is reachable here, and that is new

Mission 1.66 could reach only `OPERATOR_ATTESTED`, because a manual email send happens
inside a mail client nothing in this repository can observe. Mission 1.66.1 recorded that
ceiling honestly: the most consequential link in the chain rested on a person saying so.

A public GitHub issue has a **durable public URL**. Once the operator supplies it, the
posted title and body can be compared against the approved ones. **That ceiling was a
property of the channel rather than of manual sending**, and saying which it was is worth
more than the upgrade itself.

The upgrade path is written into the record, and the status stays
`PENDING_MANUAL_OPERATOR_ACTION` until it is walked.

## 5. Integrity checks, frozen before any post

Frozen now, which is the only time they mean anything: posted title must match the
approved title, posted body must match the frozen packet body, posted repository must
match the target, **one approval authorises exactly one public post**, a second post is
**reported as a duplicate rather than tidied away** — because a posted issue cannot be
unposted — and a divergence never repairs this approval.

## 6. Mission 1.74 was not rewritten

Its closure record still reads `enquiries_sent: 0`, `residuals_remaining: 2`, and
`dispatch_authorised_by_this_mission: false`. **All of that was true when it ran and is
still true**: the approval arrived afterwards and lives in its own document. This is the
Mission 1.66.1 shape — a later event appends a state, it does not correct a mission that
observed honestly.

**An approval to ask is not an answer.** R1's verdict is unchanged at
`R1_PARTIAL_IMPLEMENTATION_ONLY`, the qualification was not recomputed, and the tally is
still 10 PASS / 2 PARTIAL / 0 FAIL with `COUNTERPART_UNRESOLVED`.

## 7. Nothing moved

| | |
|---|---|
| public posts, GitHub issues created, `gh` invocations | 0 |
| emails sent, mailbox searches, provider contacts, enquiries sent | 0 |
| Globalping API executions, measurements, target HTTP requests | 0 |
| accounts, tokens, credential reads, first-party document requests | 0 |
| sources registered, canonical mutations, Claims, Evidence, scores | 0 |
| model calls, embeddings, migrations | 0 |

ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner arc still
parked, ADR-039 untouched.

## 8. Verification

- Gate probed with **89 deliberate violations, 89 caught** — 86 by rule, 3 by drift —
  **0 escaped**, plus **4 of 4 positive controls**.
- **One control proves the gate discriminates rather than refusing everything**: a
  correctly evidenced `BYTE_VERIFIED` send, with an attestation and an issue URL, is
  ACCEPTED. Mission 1.66 established that a gate refusing everything is not a gate.
- **A missing field is a refusal, not a crash.** Five cases delete a field the gate reads;
  each is refused rather than raising, so a truncated record cannot skip a check by not
  carrying its subject. That defect was found by the first render attempt raising
  `KeyError` on a lookup pointing at the wrong block.
- **57 new tests**; **2795 bare-python tests**; both test runners green; `ruff format --check`, `ruff check` and mypy
  all through `uv`; all **45** CI gates.

## 9. Next

**The next action is the operator's, and it happens outside this repository.**

- Post **one** public issue on `jsdelivr/globalping` under `@Speekyx`, with the approved
  title and the frozen body.
- Then supply the issue URL, so the execution record can move to `SENT` and, on
  comparison, to `BYTE_VERIFIED`.
- **`GP-R2-Q1` requires its own approval** and must not travel alongside this one.

**Mission 1.75 was not started.**
