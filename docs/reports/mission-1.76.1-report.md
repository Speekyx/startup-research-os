# Mission 1.76.1 — A reply arrived, and R2 did not close

**Outcome: `R2_REPLY_FROZEN_ATTRIBUTION_NOT_ESTABLISHED_RESIDUAL_UNCHANGED`.**

Two independent reasons keep R2 open, and **either alone would have been enough**.

---

## Reason one: nobody knows who said it

The brief asked for the sender display name, the sender email address and the sent-at
timestamp. **None of them exists in anything this repository can read.**

The operator's instruction scoped mailbox access rather than forbidding it — *"do not
access unrelated mailbox content"* — so, for the first time in this arc, a mailbox read was
**attempted**: one query, `subject:"Terms scope: HEAD measurements of publicly reachable
third-party websites"`. The Gmail connector refused it: *"This connector requires additional
permissions."* Nothing was retrieved and no unrelated content was touched.

So every header field is `null`. Not "unknown pending confirmation" — **null**, because a
sender address is exactly the field a fabricated record supplies most convincingly, and the
gate refuses any of them being non-null while the retrieval method says nothing was read.

R1's reply closed on a **raw read of a public surface**: GitHub's own `author_association`
plus an independent public-membership endpoint. A private email has no public surface at
all. Its sender lives in a mailbox, and that is the whole of the difference.

**A reply arriving in the thread is consistent with the provider having sent it and does
not establish that anyone at the provider did.** This same arc already sent this question
to an address established from three provider documents and had it bounce; address
behaviour in this thread is not assumable.

## Reason two: it answers the half that was already closed

This is the sharper finding, because **no permission grant would fix it**.

The enquiry asked four things. The reply answers one.

| clause asked | state |
|---|---|
| bounded HEAD measurements | `NOT_ADDRESSED` |
| publicly reachable third-party websites | `NOT_ADDRESSED` |
| commercial tool / commercial-purpose research | `ADDRESSED` |
| compliance with limits and policies | `ADDRESSED_AS_A_CONDITION` |

The discriminator **frozen before the send** required:

> an answer stating that the current Terms do or do not cover measuring third-party
> publicly reachable targets

The reply contains no such statement. It states permission for **commercial use** — which
is R2-A, and Mission 1.74 closed R2-A as `PERMITTED_WITHIN_TERMS` on the provider's own
FAQ. The open half is R2-B, third-party target scope, and the reply says nothing about
targets.

### The strongest argument the other way, and why it does not carry

A prohibition on using Globalping **as a proxy** only makes sense if directing measurements
at destinations the user chooses is otherwise contemplated — you cannot proxy through a
service that only measures your own infrastructure. So the carve-out arguably presupposes
third-party target use.

That is a real argument and I found it persuasive on first reading. It does not carry:
**it is an inference from a presupposition**, and Mission 1.74 graded exactly that shape
non-closing. The maintainer statement that *presupposed* redirect responses appear in
results was recorded as real evidence and not a commitment. A presupposition is not a
statement, and the discriminator asked for a statement.

**An authorised mailbox read would fix reason one and leave reason two exactly where it
is.** The probe proves this: one of its positive controls establishes the sender and R2
still does not close.

## The limitations, recorded and not dropped

| limitation | state |
|---|---|
| no abuse | `CLAIMED` |
| no exploitation of infrastructure | `CLAIMED` |
| no use as a proxy | `CLAIMED` |

`CLAIMED` rather than `ESTABLISHED`, because the speaker is not established. They are
recorded anyway: **a limitation is the part of a permission a reader is most likely to
drop, and the moment to write it down is when it is read rather than when it is needed.**

`no abuse` is a standard the reply does not bound. Recording it as a named limitation is
honest; treating it as a checkable condition would not be.

## The required report

```
R2_BEFORE                      = R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED
R2_AFTER                       = R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED
SENDER                         = NOT_ESTABLISHED
SENDER_EMAIL                   = NOT_ESTABLISHED
PROVIDER_AUTHORITY_ESTABLISHED = NO
REPLY_FROZEN                   = YES (be3845f89b636b96…, OPERATOR_SUPPLIED_TEXT)
THIRD_PARTY_PUBLIC_TARGET_USE  = NOT_ADDRESSED
COMMERCIAL_USE                 = STATED_AS_ALLOWED (by an unestablished speaker; R2-A was
                                 already PERMITTED_WITHIN_TERMS)
BOUNDED_HEAD_USE               = NOT_ADDRESSED
LIMITS_AND_POLICIES_CONDITION  = ADDRESSED_AS_A_CONDITION
NO_ABUSE_CONDITION             = CLAIMED
NO_INFRASTRUCTURE_EXPLOITATION = CLAIMED
NO_PROXY_USE                   = CLAIMED
R2_RESIDUAL_CLOSED             = NO
GLOBALPING_PASS_PARTIAL_FAIL   = 11 / 1 / 0
COUNTERPART_STATUS             = COUNTERPART_UNRESOLVED
R1_UNCHANGED                   = YES (R1_PASS_PROVIDER_DECLARED_NO_REDIRECT)
```

## What did move, and what did not

**Nothing moved.** R2-B stays `THIRD_PARTY_TARGET_SCOPE_UNRESOLVED`, the closure record
stays `UNRESOLVED`, C9 stays `PARTIAL`, the tally stays 11/1/0 and the verdict stays
`COUNTERPART_UNRESOLVED`. The qualification was not recomputed, because no input to it
changed.

The v2 dispatch record still reads `provider_replied: false`. **That is deliberate**: a
reply whose sender is not established is not a provider reply, and that record belongs to
Mission 1.74.6 rather than to this one.

The frozen v2 packet, the spent v1 dispatch record, R1 and every canonical research table
are untouched. Zero measurements, zero target requests, zero model calls, zero embeddings,
zero canonical mutations.

One counter is **not** zero: `MAIL_CONNECTOR_EXECUTIONS = 1`. An attempt that reached a
connector and was refused is a different fact from never having tried, and rounding it to
zero would hide the one action this mission took outside the repository.

## What would close R2-B

**One question, not four.** The last enquiry was compound, and a compound question invites
an answer to whichever clause the reader finds easiest — the commercial clause was already
settled and it is the one that came back.

A follow-up should name only the target-scope tension: Permitted Use says *"your internet
infrastructure"*, and the question is whether measuring a website somebody else operates
falls inside it. No commercial clause, because that half is closed.

It **requires a new operator approval** — the v2 approval authorised exactly one send and
one was made, so it is spent, and a different question is a different action. And **first**,
an authorised mailbox read would establish who replied, which is worth doing before asking
the same correspondent again.

## Verification

- Probe: **68 deliberate violations, 68 caught, 0 escaped**, plus **3 of 3 positive
  controls**, nine files restored byte for byte.
- **One escape was found and closed.** The gate originally read the record's own booleans
  for the packet relationship, so editing the frozen packet's body left them `true` and
  passed. It recomputes now — **a guard that asks a record whether it is correct is not a
  guard.**
- **The control that matters most**: a mailbox read establishing the sender, with R2 still
  open. If the gate had closed R2 there, its two reasons would have been one.
- **3129 bare-python tests**; both runners green; `ruff format --check`, `ruff check`, mypy
  over 197 files; contract and catalog `--check`; all **50** CI gates, one of them new.

## Next

Two operator actions, in this order, and neither was performed:

1. **Re-authorise the Gmail connector**, then one scoped read establishes the sender.
2. **Approve one follow-up enquiry** naming only the third-party target-scope question.

Neither closes R2 on its own. The first establishes who spoke; the second asks the question
that was not answered.

**Mission 1.77 was not started.**
