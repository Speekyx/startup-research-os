# Mission 1.65 — Dual Enquiry Dispatch Envelope Preparation V1

**Outcome: `NETLAS_RECIPIENT_PENDING_ONYPHE_ENQUIRY_FROZEN`.** One enquiry is
dispatch-ready and awaiting a single operator approval. The other is exactly where
Mission 1.64 left it, waiting on a string only a person reading a page can supply.
**Nothing was sent.**

---

## 0. The rule this mission freezes

`CONTENT_APPROVAL_IS_NOT_DISPATCH_APPROVAL`, and it decomposes into three gates
that never collapse into one:

| gate | asks | granted by |
|---|---|---|
| `CONTENT_APPROVAL` | may this exact text be sent at all | an operator approving a content hash |
| `RECIPIENT_ESTABLISHMENT` | who may read it | a first-party page, or an operator reading one |
| `CHANNEL_AUTHORIZATION` | by what mechanism | an explicit authorisation naming that mechanism |

The Netlas enquiry has held the first since Mission 1.61 and has never held the
other two. **That is why an approval issued four missions ago is still valid and
still unusable**, and why the state has not been reachable by drift.

The contract is deliberately **not** an entry in the apparatus requirement
registry. The registry governs measurement apparatuses; this governs an operator
action. The registry stays at **14** rules.

## 1. Baseline

Measured live against the deployment before any work, not recalled: 325 / 325 / 33
records, 44 Claims, 45 revisions, 58 Evidence, 1 INFERRED Claim, 1 threshold, 1
derivation, 0 refusals, 4 reliability assessments, 0 independence groups, 29
sources, 0 embeddings, no scores table, migration head `0035_refusal_provenance`,
Evidence directions SUPPORTS 57 / CONTRADICTS 1, claims carrying both directions
0. **Drift from Mission 1.64: none.**

Precondition: `HEAD` = `origin/main` = `c18a766`, clean tree, PR #107 MERGED.

The approved Netlas body was re-verified against its hash
`310acf28…a049c4`. It **matches**, and no recipient, sender, channel, wording
change, normalisation or approval metadata was written into it.

## 2. The circularity an envelope hash has to survive

Mission 1.56 settled the frozen-document shape: a document's hash lives **outside**
the bytes it hashes, because writing it in changes what it was computed over.

An envelope cannot do that. The thing an operator approves **is** the envelope, so
the hash has to be inside it. The resolution is to hash a named set of **binding
fields** rather than the file:

```
enquiry_document_id · enquiry_content_sha256 · recipient_address
outbound_channel · sender_identity · subject · content_version
```

canonicalised as sorted, separator-tight JSON. Excluded: the envelope hash itself,
the approval string, the recorded date, and every sentence explaining how the
recipient was established. So recording the hash does not move it — and that is
**recomputed from the file as stored** by both the renderer and a test, rather
than asserted.

    content   0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f
    envelope  12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2
    approval  APPROVE MISSION 1.65 DISPATCH 12a62853…5b4fe0d2

**The digest binds the ACTION rather than the document.** Changing the recipient,
the channel, the sender, the subject or the content hash moves it. Changing when
the record was written, or how the provenance is worded, does not. That is the
Mission 1.64 finding — an approval of text is not an approval of a channel — made
mechanical.

## 3. The recipient, and why provenance rather than spelling decides it

The ONYPHE address was retrieved from **two** first-party pages, each printing it
as a live `mailto` link: the about page, labelled *Contact us*, and the site root's
header navigation, labelled *Contact From Web site*.

Its local part is a conventional word — and Mission 1.64's validator listed exactly
that string among the mailbox forms it refuses. **That rule forbids INFERRING a
mailbox from convention. This one was not inferred; it was read.**

So the check is on how the address was obtained, never on how it is spelled. A
string ban would have refused a correctly established address while still admitting
a guessed one that happened to look unusual, which is the wrong way round.

The record also says what the route is **not**: a general contact mailbox, not a
dedicated technical or support channel. No such channel is published, and claiming
one would be a fact about the provider that nobody established.

**Three published addresses were seen and excluded by name:**

| purpose as printed | excluded because |
|---|---|
| a personalised demo | writing to it would be requesting a trial, and a zero-cost trial destroys preregistration exactly as a paid one would |
| sales, printed obfuscated | the enquiry is not a commercial approach, and the address was not resolvable without reconstruction |
| an abuse mailbox, mentioned only inside published scanning principles | not published as this provider's own contact route; reconstructing it would be inventing an address |

## 4. An envelope that names nobody carries no hash

The Netlas envelope is a **template**, not an action:

    state              INCOMPLETE_RECIPIENT
    recipient_address  null
    outbound_channel   NOT_EVALUATED
    envelope_sha256    null
    approval_string    null
    approvable         false
    packet_generated   false

A hash is an approval handle. Producing one for an incomplete action would let an
operator approve a send whose reader is blank. A channel is evaluated for an
action, and there is no action while the recipient is unknown — binding a route to
an envelope naming nobody would be preparing to send to a blank.

**The obfuscated page was not re-fetched.** Missions 1.62, 1.63 and 1.64 each
established that automated retrieval returns a placeholder there; a fourth attempt
would return the same placeholder and cost a retrieval. No mailbox was guessed and
no obfuscation was decoded.

## 5. The channel, and the connector that was not used

    outbound_channel   OPERATOR_MANUAL_SEND
    connector_state    AVAILABLE_NOT_AUTHORIZED
    sender_identity    OPERATOR_CHOSEN_MAILBOX_AT_SEND_TIME  (placeholder)

A mail-capable connector exists in this runtime. **Its presence is not an
authorisation to use it**: sending from the operator's own account is an outward
action on their behalf, and only an already-authorised mechanism qualifies. The
record says why it was not selected rather than leaving its presence unexplained.

The sender is a **placeholder**, permitted for `OPERATOR_MANUAL_SEND` only —
because under manual send the sender genuinely is not determined until the operator
sends, and binding a mailbox they did not choose would record a fact nobody
established. **Its cost is stated rather than hidden**: the hash then pins three of
four fields. If the operator names the mailbox, a re-frozen envelope binds all four
and carries a different hash, and this one becomes `SUPERSEDED` rather than edited.

## 6. The ONYPHE enquiry

Exactly the three residuals Mission 1.64 froze, with **no fourth added**:

1. **Record lifecycle** — does each scan create a distinct document with its own
   collection timestamp, or is one document updated in place? (decides B2)
2. **Datascan port set** — which TCP ports, is 22 among them, and is the set's
   composition recorded against a date or a configuration version? (decides B4 and
   `APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE`)
3. **Fields retained beyond thirty days** — do the address, the collection
   timestamp and the scanner node fields survive? (decides B4 and B6)

It asks for **no records, no account, no API key, no trial, no demo and nothing
commercial**. Nothing already documented is re-asked: question 3 states the known
4 KB truncation of the raw field as known and explicitly declines to raise it
again, because asking a provider to restate its own documentation wastes the one
question that can be asked.

And **it asks what the system does, never whether the system qualifies.** Asking a
provider to confirm its API is observation-addressable would be asking it to grade
our gate.

The hash of its rendered form lives in the dispatch envelope, never in the enquiry.

## 7. Two things this mission's own tooling caught

**The validator refused this mission's record**, `testing-strategy.md` §23 for the
seventh time. The preamble's sentence *denying* that the enquiry asks for anything
commercial contained the forbidden word — inside the sendable body, where the scan
is strictest and should be. Reworded to state the rule without reciting it, rather
than scoping the scan around a denial: scoping is how a structural check stops
checking.

**The probe caught its own defect before the gate did.** One case substituted a
heading absent from the approved document, so it mutated nothing and reported an
escape from a gate that was working — the exact Mission 1.64 shape. It is now
structurally impossible: every case asserts the bytes moved before the gate is
asked about them.

## 8. Nothing moved

| | |
|---|---|
| enquiries sent | 0 |
| connector executions | 0 |
| first-party retrievals | 2 |
| measurement queries / counts / hosts / banners / downloads | 0 |
| trials / purchases / credentials written | 0 |
| apparatus gates changed | 0 |
| pairs compared / ranked / selected | 0 |
| canonical mutations, sources, reviews, Claims, Evidence | 0 |
| model calls, embeddings | 0 |

Apparatus states are exactly where Mission 1.64 left them: Netlas A7 PASS / A8
PARTIAL, ONYPHE B2 PARTIAL / B4 PARTIAL, LeakIX and Shadowserver
`INDIVIDUALLY_NOT_QUALIFIED`. **Qualified 0 of 4, so `PAIR_ANALYSIS_NOT_READY`.**

**Question drafted is not answered. Question approved is not answered. Question
sent is not answered.** Only a reviewed first-party response may move a gate.

## 9. The asymmetry, and why it is not a preference

One provider prints its contact address as a live link on two pages. The other
serves it through an anti-scraping mechanism. **Nothing about either fact bears on
whether the apparatus is a good measurement instrument.**

It would be easy to read dispatch readiness as progress on the apparatus. It is
progress on the **asking**, and the gates are exactly where they were.

## 10. Verification

- Validator probed with **204 deliberate violations, 204 caught**, four of which
  edited the approved Netlas document. Every case asserts it mutated the bytes.
- **51 tests** in `packages/inferred-claim-evaluator/python/tests/test_dispatch_envelope.py`.
- CI gate **33**: `render_dispatch_envelope.py --check`, which recomputes both
  hashes on every run, so an edit to the approved body or to the bound action turns
  the gate red rather than leaving an approval beside different bytes.

## 11. Next

**`STOP_FOR_DISPATCH_APPROVAL`.**

One approval is available now — `APPROVE MISSION 1.65 DISPATCH <envelope hash>`,
authorising the frozen ONYPHE text to be sent once, to the established recipient,
by the operator manually.

One input is still missing — the exact address displayed on the Netlas legal page,
which renders in a browser and not to an automated retrieval.

**Mission 1.66 — Approved Dispatch Execution V1** may send exactly the envelopes
whose hashes were approved, once each, and record delivery provenance. It may not
send an unapproved envelope, send either enquiry twice, infer authorisation from
content approval or from a connected account, treat a dispatch as an answer, or
edit either frozen enquiry. **Mission 1.66 was not started.**
