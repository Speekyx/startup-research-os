# Mission 1.74.6 — The send is attested, the delivery is not

**Outcome: `R2_V2_DISPATCH_OPERATOR_ATTESTED_DELIVERY_UNCONFIRMED`.** The operator sent
the approved GP-R2-Q1 v2 email once, by hand, and attested to it. **No mailbox was read,
no connector was used, and this repository sent nothing.**

---

## 0. What is now recorded

| | |
|---|---|
| execution | `SENT` |
| sent at | `2026-09-06T19:39:00+04:00` |
| sender | `thib.chm@gmail.com` |
| recipient | `d@globalping.io` |
| attestation level | `OPERATOR_ATTESTED` |
| **delivery** | **`UNCONFIRMED`** |
| provider contacted | **false** |
| provider replied | **false** |
| message id | **null** |
| approval | **exhausted** |

## 1. A send is not a delivery

This is the whole mission. The attestation says a message was sent; it says nothing
about whether it arrived, and **nothing here may look**.

So the record separates the two. `deliveries_confirmed` stays 0, `delivery_status` reads
`UNCONFIRMED`, and `provider_contacted` stays **false** — because a contact means
something reached the provider, and only delivery would establish that.

**This arc supplies its own proof that the two come apart.** The v1 message to
`legal@globalping.io` was sent too, and then it bounced. Had that record marked a contact
at the moment of sending, it would have been wrong within the hour.

The distinction is now a gate rule rather than a sentence: `UNCONFIRMED` forbids a counted
delivery and forbids `provider_contacted`; `CONFIRMED` must name **what** established it,
and **may not name the attestation of sending** — that specific inference is refused by
name.

## 2. Silence is not an observation

The record does **not** say "no bounce was reported". It says the attestation is silent on
delivery, and that nothing here looked.

Those are different claims. "No bounce reported" implies someone checked a mailbox; nobody
did, and the record was written minutes after the send, sooner than a bounce would
necessarily arrive. The field is `absence_of_a_reported_bounce_is_not_evidence`, and the
gate refuses it being false.

**The state can still move.** A later bounce sends this to
`DISPATCH_ATTEMPTED_DELIVERY_FAILED`, and the gate's failure branch was widened to admit
it: a bounce can follow a dispatch that really happened, so a failure no longer resets the
count of dispatches. What a failure forbids is a delivery, a contact and a level.

## 3. The sender is attested, not checked

Mission 1.74.5 left the sending mailbox unbound at the operator's instruction, and **stated
that cost in advance**. This is the record of paying it: `thib.chm@gmail.com` is in the
record because the operator said so, and that is the whole of the evidence for it.

The approval keeps its placeholder. **Writing the real mailbox back into it would make an
unpinned field look pinned** and make this address read as approved before the fact, which
it was not — so the gate refuses that write-back explicitly, from the execution side.

## 4. Nothing was invented to fill a field

- **No message id.** The attestation carries none, and the only route to one runs through
  the sending mailbox. The field is `null`, and the gate refuses a non-null value — because
  a plausible id is exactly what a fabricated record would contain.
- **No body comparison.** What left the mail client has not been seen here. The record says
  the frozen body was used *per the attestation*, and separately that this repository did
  not compare it.
- **No reply.** None was reported. A reply is a document: it would be frozen verbatim in
  its own record before anything interpreted it, and the gate refuses this record claiming
  one.
- **No timestamp without an offset.** A naked local time names no instant. The gate requires
  the offset and refuses a send attested as happening before the approval that authorises it.

## 5. A sent question is still not an answer

R2's verdict is unchanged, 0 residuals closed, R2 not closed, R1 untouched, and the
qualification was **not** recomputed — neither in general nor from the fact of dispatch,
which is now a separate refusal. A question in flight is an act by us, not evidence about
the provider.

The mission counters stay at zero, because they count what **this repository** did, and it
did nothing: 0 emails sent here, 0 connector executions, 0 mailbox searches, 0 documentation
requests. The operator's send lives in the execution block, where it belongs.

The v2 packet is byte-identical, still reads `send_status: NOT_AUTHORIZED`, and still
records no approval of its own. The approval's own digest recomputes unchanged, which is
what the envelope rule was for: execution, date and sender were excluded from it in advance,
so recording an execution could not disturb it.

## 6. Verification

- Gate probed with **97 deliberate violations, 97 caught** — 96 by rule, 1 by drift —
  **0 escaped**, plus **3 of 3 positive controls**.
- **Six cases repair the hash before attacking**: four keep the packet's file hash in step
  with the edit, and two recompute the spent approval's own digest. Without them the outer
  guard caught every one of those edits for the same reason, and the checks behind it were
  never asked anything.
- **The controls are the point.** A delivery confirmed by a source that is *not* the send
  attestation passes; **this send bouncing later** passes. A gate that could only express
  success would force the next outcome to be recorded as something it is not.
- Eighteen of the module's 78 tests now run the gate's own checks against mutated dicts
  rather than reading its source, because **a refusal spelled in a module is not a refusal
  until something calls it**.
- **2979 bare-python tests**; both runners green; `ruff format --check`, `ruff check` and
  mypy through `uv`; all **48** CI gates.

## 7. Next

**The operator waits.** If a reply arrives it is forwarded and frozen verbatim before
anything interprets it. If a non-delivery report arrives instead, it is attested and this
dispatch moves to `FAILED` — and that would exhaust the second approval as the first was
exhausted, so a third recipient would need its own review and its own approval.

No deadline is recorded, because none was agreed, and **silence would close nothing**.

**Mission 1.75 was not started.**
