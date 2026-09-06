# Mission 1.74.4 — The designated address bounced

**Outcome: `R2_DISPATCH_ATTEMPTED_DELIVERY_FAILED_REPLACEMENT_PREPARED`.** The operator
attempted the approved GP-R2-Q1 email exactly once and it was rejected. The approval is
spent, a replacement recipient was reviewed and established, and a second packet is
prepared and **unapproved**.

---

## 0. A bounce is not a send, and it is not a contact

| | |
|---|---|
| status | `DISPATCH_ATTEMPTED_DELIVERY_FAILED` |
| attempts | 1 |
| sends / deliveries | **0 / 0** |
| provider contacted | **false** |
| attestation level | **none** |

**`provider_contacted` stays false** because nobody received it. An attempt that bounced
is not a contact, and recording it as one would put a conversation in the record that
never began.

**No attestation level applies.** The levels grade evidence that a message *was*
delivered; nothing was. Recording `OPERATOR_ATTESTED` here would grade the evidence for
an event that did not happen — so the attestation is marked as being **of a failure
rather than of a send**, which is a distinction the record now carries structurally.

**The non-delivery report was not imported.** Reading the operator's mailbox for a bounce
message would replace an attestation with an inference and require an access nobody
requested — Mission 1.66's reasoning, applied to a failure instead of a send.

## 1. The approval is exhausted by the attempt

One send was authorised and one was attempted. A retry to the same address would be a
second use of a one-use approval; a send to a different address is **a different action**,
because the recipient is one of the bound fields. Both are refused, and the replacement
**requires a new explicit operator approval** that does not exist.

The approval's own digest did not move: the execution section changed, the binding fields
did not.

## 2. A supplied address is a claim, and is established on provenance or not at all

`d@globalping.io` arrived in an instruction. **That is not why it is accepted.**

Mission 1.65 judged a recipient on provenance rather than on spelling, and refused to
infer one from convention. The same standard applies to one handed over — so four
first-party surfaces were read:

| surface | addresses | designates for |
|---|---|---|
| Terms of Use §16 | `legal@globalping.io` | questions about these Terms |
| Privacy Policy §12 | `legal@globalping.io` | questions about this Privacy Policy |
| Cookie Policy | `legal@globalping.io` | the Data Protection Team |
| website footer, **committed source** | `d@globalping.io` | general contact |

The establishing read is the provider's own committed source —
`jsdelivr/globalping.io`, `src/views/components/footer.html`:

```html
<li><a href="mailto:d@globalping.io"> d@globalping.io</a></li>
```

The rendered homepage agrees, and is recorded as **corroboration only**, because that
retrieval went through a summarising extraction and Mission 1.63 established that a
summary is not a document.

**A single-letter local part is not treated as disqualifying.** A string rule would refuse
a correctly established address while admitting a guessed one that happened to look
ordinary — which is exactly the failure Mission 1.65 named.

## 3. An established general contact is not a designated channel

This is the distinction most easily lost, and it is the same over-read this arc has
refused for a schema, for product design and for a FAQ answer.

**`ESTABLISHED_FIRST_PARTY_GENERAL_CONTACT_NOT_THE_TERMS_DESIGNATED_CHANNEL`.** Three
provider documents designate `legal@globalping.io`. Not one designates the footer
address. Calling it designated would assert a standing no provider document gives it.

What makes it *relevant* is weaker and is written down as weaker: the designated route is
unreachable, and this is the only other address the provider publishes — the remaining
first-party route to the same organisation.

**And the tension is recorded rather than smoothed:** the provider's own current documents
designate an address that does not accept mail, while a different address is published
and live on its homepage. This record does not resolve that, and it is not evidence that
the general address is monitored, answered, or appropriate for a Terms question.

**One rejection is not a permanent fact about an address.**
`OPERATOR_ATTESTED_DELIVERY_REJECTED_ONCE`, explicitly **not**
`PERMANENTLY_NONEXISTENT`.

## 4. The replacement packet

| | v1 | v2 |
|---|---|---|
| recipient | `legal@globalping.io` | `d@globalping.io` |
| channel | `PROVIDER_DESIGNATED_TERMS_CHANNEL` | `PROVIDER_PUBLISHED_GENERAL_CONTACT_CHANNEL` |
| subject / body | — | **identical** |
| digest | `713d62c9…` | `987f3ff5…` |
| send status | `NOT_AUTHORIZED` | `NOT_AUTHORIZED` |

**The subject and body are preserved exactly.** A sentence explaining that the designated
address bounced was considered and **not** added: nothing about the question changes with
the recipient, and adding prose would make this a differently worded enquiry the operator
has not read.

**The channel label changed**, because reusing v1's would assert a designation this
address does not have.

**v1 is superseded, not edited.** It still answers to its own hash. It recorded a
correctly established address that later rejected delivery — a fact about the provider,
not an error in the record.

## 5. The shared question id, and what defeats it

Both packets carry `question_id: GP-R2-Q1`, because it is the same question. That creates
a real hazard: an exhausted approval appearing to cover a new recipient.

**The hash defeats it.** The approval binds `approved_content_sha256`, and the digests
differ because the recipient and channel differ. So the spent approval **cannot name**
this packet — enforced by arithmetic rather than by a rule somebody has to remember. The
gate checks it from both directions.

## 6. Nothing moved

| | |
|---|---|
| emails sent **by this repository**, connector executions, mailbox searches | 0 |
| emails delivered | 0 |
| provider contacts | 0 |
| approvals created | 0 |
| residuals closed, qualification recomputed | 0 |
| Globalping API executions, measurements, canonical mutations, model calls | 0 |

Failed delivery attempts **by the operator**: **1**, counted separately — because this
repository acting and the operator acting are different facts, and flattening them would
lose the distinction the whole arc is built on.

Six first-party documentation requests. R1 is untouched at `SENT` / `OPERATOR_ATTESTED`.

## 7. Verification

- Both gates probed with **64 deliberate violations, 64 caught** — 61 by rule, 3 by
  drift — **0 escaped**, plus **4 of 4 positive controls**.
- **One control is inverted and is the important one**: a review that establishes
  *nothing* must **block** the packet bound to it. A gate that only ever accepts is not a
  gate, and a gate that only ever refuses is not one either — so three controls prove
  legitimate variants pass (a genuinely designated replacement, a different established
  address, a reworded body that stops claiming preservation) and one proves an
  unestablished address is refused.
- **The probe's writes are now all retried.** This machine intermittently rejects writes
  to these files, and a probe that dies mid-case leaves a record edited on disk —
  Mission 1.67's finding, met three times in this arc now. Hardening `restore()` alone was
  not enough, because the crash happened on a *case* write.
- **Four Mission 1.74.2 tests asserted the pre-attempt state and were re-pointed**, not
  deleted. One of them iterated every accounting counter asserting zero; it now excludes
  the counter the **operator** owns, and a new test asserts that counter is 1 while
  deliveries and repository-sent mail are 0.
- **2901 bare-python tests**; both runners green; `ruff format --check`, `ruff check` and
  mypy through `uv`; all **47** CI gates.

## 8. Next

**Nothing may be sent.** The replacement packet is prepared and carries no approval; a new
recipient is a new action and needs a new explicit operator approval naming its digest.

If that approval is given, the mechanism question returns with it: the ceiling for this
channel is still `OPERATOR_ATTESTED`, because it is still manual email.

**Mission 1.75 was not started.**
