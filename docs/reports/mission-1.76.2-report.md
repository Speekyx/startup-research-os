# Mission 1.76.2 — One question, and it is the one that was not answered

**Outcome: `R2_B_FOLLOWUP_PACKET_READY_FOR_OPERATOR_APPROVAL`.**

Nothing was sent, no mailbox was touched, and no verdict moved.

---

## Report

```
PACKET_ID                    = GP-R2-B-Q1
PACKET_VERSION               = 1
MECHANISM                    = OPERATOR_MANUAL_REPLY_IN_EXISTING_EMAIL_THREAD
THREAD_SUBJECT               = Terms scope: HEAD measurements of publicly reachable
                               third-party websites
RECIPIENT_REQUIRED           = NO
RECIPIENT_ESTABLISHED        = NOT_APPLICABLE (DETERMINED_BY_THE_THREAD_NOT_SUPPLIED)
CONTENT_SHA256               = fe312c37b8622e5abbdaaa541d00189c5a4a2f78b7082d3f70a034b7413da4dc
SEND_STATUS                  = NOT_AUTHORIZED
OPERATOR_APPROVAL_RECORDED   = false
MAX_SENDS                    = 1
R2_BEFORE                    = R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED
R2_AFTER                     = R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED
R2_B_RESIDUAL                = THIRD_PARTY_TARGET_SCOPE_UNRESOLVED
GLOBALPING_PASS_PARTIAL_FAIL = 11 / 1 / 0
COUNTERPART_STATUS           = COUNTERPART_UNRESOLVED
OUTWARD_ACTIONS_PERFORMED    = 0
```

**FROZEN_BODY:**

> Thanks for confirming the commercial-use point.
>
> Just to clarify the remaining part of my question: does Globalping permit bounded HTTP
> HEAD measurements of publicly reachable third-party websites that I do not own or
> operate, provided the measurements comply with Globalping's limits and are not abusive,
> exploitative, or used as a proxy?

## Why `RECIPIENT_REQUIRED = NO`, and why that is not a dodge

The brief said to stop with `EXACT_REPLY_RECIPIENT_REQUIRED` **if the repository requires
an exact recipient email to authorize a manual reply**. It does not — for this mechanism.

The two earlier approvals bound a `recipient` because their mechanism was
`OPERATOR_MANUAL_EMAIL`: composing a fresh message, where the operator types an address and
an unbound one could send the message anywhere. **A reply inside a thread inherits its
recipient.** Nothing is typed, so there is nothing to pin.

So the digest binds the **thread** instead, by three values:

| bound | |
|---|---|
| thread subject | the v2 packet's subject, unchanged |
| prior enquiry digest | `987f3ff57ce661c6…` |
| prior reply digest | `be3845f89b636b96…` |

That is **tighter than an address**, not looser: it pins the conversation, the question
that opened it and the reply being answered. An address would have identified a mailbox and
said nothing about which exchange the reply belongs to.

And the alternative was not available. The sender of the reply being answered is
`NOT_ESTABLISHED` — Mission 1.76.1 attempted the mailbox read and the connector refused it.
Writing an address here would have **invented the one field the whole exchange hangs on**.
The field carries the sentinel `DETERMINED_BY_THE_THREAD_NOT_SUPPLIED`, and the gate refuses
an `@` appearing in it.

## Why a new packet rather than a v3 of the old one

`GP-R2-Q1` asked four things and **was answered**. This asks one of them again, alone,
which is a different question rather than a further version of that one.

That matters mechanically: a new question must not be reachable by an approval written for
the old one. Both earlier approvals are spent — the first by an attempt that bounced, the
second by the one send it authorised — and each names a different content digest **and** a
different question id. The gate asserts both live, so an edit that retargeted a spent
approval at this packet fails there rather than passing quietly.

## One question, and not the settled one

The last enquiry was compound, and **a compound question gets the easiest clause
answered**. The commercial clause was already closed in Mission 1.74 on the provider's own
FAQ, and it is the one that came back.

So this body carries **exactly one question mark**, says nothing about commercial use
beyond acknowledging the answer already given, and names the three things the question is
about: `HEAD`, `third-party`, and `do not own or operate`. The gate counts the question
marks and refuses a second.

Not broadened to arbitrary methods, GET body retrieval, scanning, proxying, infrastructure
exploitation, unlimited traffic, or any target the operator does own.

The wording is the operator's. The only change is **line wrapping** — their text was
hard-wrapped for the brief, and every packet in this arc stores paragraphs unwrapped
because that is what gets pasted into a mail client. Both forms are stored, and the gate
checks that whitespace-normalised they are identical, so "only the wrapping changed" is a
check rather than a claim.

## The discriminator, frozen before dispatch

R2-B closes only on a reply that explicitly establishes one of **`PERMITTED`**,
**`NOT_PERMITTED`** or **`CONDITIONALLY_PERMITTED`** — and the answer must address
third-party target scope **explicitly**.

It does not close on silence, on a generic commercial-use permission, on "publicly
reachable target" appearing only in technical API documentation, on product behaviour, on
the proxy limitation alone, on absence from the prohibited-use list, or on implication or
presupposition.

**The presupposition route is listed with its reason attached.** Mission 1.76.1 found the
strongest available argument that the last reply answered R2-B — a no-proxy carve-out
presupposes third-party targets — and refused it. Writing that into the discriminator stops
the same argument being rediscovered as a novelty by whoever reads the next reply.

**`NOT_PERMITTED` is a resolving answer.** A discriminator that only admitted a yes would
be a wish: it would make a refusal unrecordable and leave R2-B open however the provider
answered.

## Authority stays a separate gate

The earlier sender is still `NOT_ESTABLISHED`, and this mission does not claim otherwise.
That does **not** block preparing this packet — the gate refuses the record saying it does —
and preparing it does not establish anyone.

It does affect what a reply would be worth. A reply in this thread inherits the same
attribution problem, so **establishing the sender remains a separate and still-open
action**, and it is worth doing before asking the same correspondent again.

## Verification

- Probe: **74 deliberate violations, 74 caught, 0 escaped**, plus **3 of 3 positive
  controls**, ten files restored byte for byte.
- All eight cases the brief names are covered, in the form available at this stage: no
  approval record exists yet, so *"old approval reused"* is probed by pointing each spent
  approval at this packet's digest **and** at its question id, and *"second send"* by the
  packet authorising other than exactly one outward reply. Saying which form was possible
  is part of the result.
- **Binding-field mutations are re-digested before the gate sees them**, so the content
  checks have to do the work instead of hiding behind the hash check.
- **The controls are the point**: an explicit permission and an explicit prohibition must
  both resolve, and a reworded body that still asks exactly one question must still pass.
  A gate that only accepts the sentence we happened to write is a wall.
- **3171 bare-python tests**; both runners green; `ruff format --check`, `ruff check`, mypy
  over 197 files; contract and catalog `--check`; all **51** CI gates, one of them new.

## What did not move

R2-B stays `THIRD_PARTY_TARGET_SCOPE_UNRESOLVED`, C9 stays `PARTIAL`, the tally stays
11/1/0 and the verdict stays `COUNTERPART_UNRESOLVED`. **Preparing a question resolves
nothing**, and the gate asserts that too.

`GP-R2-Q1` v1 and v2, both their approvals, both execution records, their frozen hashes and
the received-reply source record are untouched. Zero emails, zero Gmail reads or writes,
zero connector calls, zero GitHub writes, zero measurements, zero target requests, zero
research API calls, zero model calls, zero embeddings, zero canonical mutations.

## Next

**One operator decision: approve or refuse exactly one outward reply of this packet in the
existing thread.** It was not requested inside the repository and no approval record was
created.

Separately and still open: establishing who sent the earlier reply, which an authorised
mailbox read would settle and which no amount of asking again will.

**Mission 1.77 was not started.**
