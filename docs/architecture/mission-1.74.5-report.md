# Mission 1.74.5 — The second approval, and the first one stays spent

**Outcome: `R2_V2_DISPATCH_APPROVED_AWAITING_MANUAL_OPERATOR_ACTION`.** The operator
approved exactly one manual email dispatch of the v2 packet to `d@globalping.io`.
**Nothing was sent, no connector was used, and no mailbox was read.**

---

## 0. What was approved

| | |
|---|---|
| enquiry | `GP-R2-Q1` **v2** |
| mechanism | `OPERATOR_MANUAL_EMAIL` |
| recipient | `d@globalping.io` |
| channel | `PROVIDER_PUBLISHED_GENERAL_CONTACT_CHANNEL` |
| subject | Terms scope: HEAD measurements of publicly reachable third-party websites |
| sender | `PLACEHOLDER_PERMITTED_FOR_MANUAL_SEND_ONLY` |
| maximum sends | **1** |
| approval hash | `41590d55…` |
| execution | `PENDING_MANUAL_OPERATOR_ACTION` |

## 1. A quoted digest is recomputed, not copied

The approval arrived carrying a content hash. **Copying it would have made the approval
name whatever the instruction said rather than whatever the packet is.**

So the digest was recomputed from the packet as stored, and the record keeps **both** —
the stated value and the recomputed one — with the gate refusing them disagreeing. That
turns a quoted string into a check that could have failed. It did not: they match, and
the assertion passed silently, which is what a check looks like when the world is in
order.

The packet's own file hash is recorded too, so an edit after the approval is detectable.

## 2. The sender stays open, at the operator's instruction

The operator stated the sending mailbox is chosen at execution time. That is the same
property **Mission 1.65 recorded in advance** for a manual mail send: the sender is not
determined until the send.

So the approval binds the enquiry, the packet version, the content digest, the mechanism,
the recipient, the channel, the subject and the send limit — and **not** the sender. The
cost is unchanged and is stated: this approval pins the action apart from the mailbox it
leaves from. A real mailbox written into that field would be a **different approval**, and
the gate refuses one.

## 3. A second approval is not a renewal of a spent one

| | first | second |
|---|---|---|
| recipient | `legal@globalping.io` | `d@globalping.io` |
| execution | `DISPATCH_ATTEMPTED_DELIVERY_FAILED` | `PENDING_MANUAL_OPERATOR_ACTION` |
| provider contacted | false | false |
| approval hash | `90fd201d…` | `41590d55…` |

The recipient changed, and the recipient is a bound field, so this **authorises a
different action** rather than extending a spent one. The two approvals name different
content digests, different recipients and different approval digests; **neither can stand
in for the other.**

**The first approval was not reused, not reinterpreted, and not repaired.** The gate
asserts, live, that it still reads exhausted, that its attempt still reads a failure, and
that its `provider_contacted` still reads false — so a later edit that quietly
rehabilitated the bounce into a delivery **fails here** rather than passing quietly.

It gained exactly one appended forward pointer, its own digest unchanged: Mission 1.66.1's
shape, used for the third time in this arc.

## 4. The ceiling belongs to the medium, not to the address

The address changed. The medium did not. So Mission 1.66's ceiling is unmoved:
`BYTE_VERIFIED` stays **unreachable**, the reachable set is exactly `OPERATOR_ATTESTED`,
and the upgrade path reads **NONE**.

That is worth saying plainly because the temptation runs the other way — a *new* channel
invites the thought that its properties might be new too. They are not: a mail client's
outbox is something no guard here can observe, whichever address the mail is going to.

## 5. Nothing has been performed

| | |
|---|---|
| send attempts, sends, deliveries | 0 / 0 / 0 |
| provider contacted | **false** |
| emails sent by this repository, connector executions, mailbox searches | 0 |
| operator attestation, attestation level | none |

Every accounting counter is zero. The packet is byte-identical and still reads
`send_status: NOT_AUTHORIZED`, recording no approval of its own — because the approval
lives beside it, which is the discipline that keeps the packet's own field honest.

**An approval to ask is not an answer.** R2's verdict is unchanged, no residual closed,
the qualification was not recomputed, and R1 was not touched.

## 6. Verification

- Gate probed with **95 deliberate violations, 95 caught** — 92 by rule, 3 by drift —
  **0 escaped**, plus **3 of 3 positive controls**.
- **One control is the one that matters most**: this approval **bouncing too** is a
  representable state. A gate that could only express success would force the next failure
  to be recorded as something it is not.
- **Eleven of the violation cases attack the spent approval rather than this one** —
  rehabilitating it to `SENT`, resetting it to pending, turning its bounce into a contact,
  un-exhausting it, breaking its digest, retargeting it at the new recipient. All eleven
  are refused, which is what makes "not a renewal" a check rather than a sentence.
- **2944 bare-python tests**; both runners green; `ruff format --check`, `ruff check` and
  mypy through `uv`; all **48** CI gates.

## 7. Next

**The operator sends one email to `d@globalping.io`** with the approved subject and the
frozen body, from a mailbox of their choosing, and then attests to it. This repository may
not perform it, and an attestation is the only evidence this channel can produce.

If that attempt also bounces, the approval is exhausted again and a third recipient would
need its own review and its own approval — the integrity rules already say so.

**Mission 1.75 was not started.**
