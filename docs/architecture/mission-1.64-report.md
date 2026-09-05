# Mission 1.64 — Anchor Enquiry Dispatch & ONYPHE Residual Closure V1

**Outcome: `ANCHOR_CONTACT_CHANNEL_STILL_NOT_ESTABLISHED`.** An approved message,
a hash that verifies under every plausible boundary, a mail-capable connector in
the environment — and nothing sent.

---

## 0. An approval names a document, not a recipient

The frozen enquiry records its recipient as `TO_BE_SUPPLIED_BY_OPERATOR`. The
address travels in a dispatch packet **beside** the document rather than inside
it, because writing a real address into the body would change its bytes and void
the approval.

That design was made in Mission 1.61, before anyone knew the address would be hard
to get. It is why an approval issued three missions ago is still valid today.

## 1. Baseline and the hashing boundary

Verified live, no drift: 325 / 325 / 33 records, 44 Claims, 45 revisions, 58
Evidence, 1 INFERRED Claim, 4 reliability assessments, 0 independence groups,
head `0035`, main `2430a02`.

The approved digest was recomputed three ways:

| boundary | matches |
|---|---|
| raw bytes as stored | yes |
| UTF-8 decode and re-encode | yes |
| CRLF normalised to LF | yes |

All three agree because the file is LF-only. **That is worth recording rather than
assuming**: on a Windows working tree a line-ending rewrite would have split them,
and a mission that tested one boundary would not know which one the approval
named.

The document also survives regeneration by its own renderer byte for byte, which
two CI gates now enforce together.

## 2. Three independent reasons not to send

Recorded in order, so a later mission knows which to clear first.

1. **No verified recipient.** The address on the published legal page is served
   through an obfuscation mechanism, so automated retrieval returns a placeholder.
2. **An approval of text is not an approval of a channel.** Sending from the
   operator's own account is an outward action on their behalf. They approved the
   enquiry's *content*; they have not asked for it to be sent from their mailbox.
3. **Only an already-authorised mechanism qualifies.** A mail-capable connector
   being present in the environment is not an outbound route this repository
   holds a standing authorisation to use for research correspondence.

Any one would have been sufficient.

**No mailbox was guessed and the obfuscation was not decoded.** The address is
published for people to read, and a person reading it is the route the publisher
intended. Defeating an anti-scraping mechanism to obtain it is circumvention, and
a guessed mailbox would put an unapproved recipient beside an approved message.

## 3. Four converging statements are not a statement

The candidate's record-lifecycle question gained real supporting evidence from
four documented places:

> Query data collected some hours ago

> By default, latest result is displayed first on output

> the last 10 or 100 results for given category of data and only for the last 30-days

> the summary will be composed of data fetched in the last 30-days only, you
> cannot query historical data with that endpoint

Latest-first ordering presupposes several results with different times. A hundred
results per category per asset in thirty days is far more than one weekly cycle.
An endpoint excluded from historical querying implies a historical surface exists.

**And none of them states the model.** Every one is fully explained by one document
per service per port with no repetition over time — an address exposing twenty
services produces the same numbers either way.

**B2 stays `PARTIAL`.** The residual is now one named case:

> A service is observed **during** window W, and observed again **after** W.

An append store returns it for W. A maintained store does not, because its single
record's timestamp has advanced past W — so a windowed count loses exactly the
hosts that persist. Nothing documented decides it, and the easier case (observed
only before and after) discriminates nothing, because both models exclude it.

## 4. The port question is now an established gap

The published scanned-port list was asked directly for every category section it
carries. It carries exactly one, and it is not the relevant category. The datascan
set is documented by **size** and **cadence** and never by **membership**.

Neither direction was inferred: nothing says datascan excludes port 22 either.

## 5. Retention, asked in the second place it could live

The retention page names no removed fields. This mission looked in the field
documentation itself, on the reasoning that a per-field annotation would live
beside the field it governs. There is none, for any field.

So whether the address, the observation timestamp and the scanner node fields
survive stays `UNKNOWN` — **and was not guessed in either direction.** Reasoning
that a scan archive without addresses would be useless, so they must survive, is
an argument from what a sensible provider would do rather than from what this one
documents.

`MAX_FULL_FIDELITY_RETRIEVAL_DELAY` stays 30 days. B3 is not reopened: the raw
field is named as *truncated*, which places it outside the set *removed*.

## 6. The probe found a real gap in my own validator

Marking the frozen enquiry as **sent** escaped.

The validator checked the dispatch record's send state and never the frozen
document's own delivery fields — a check Mission 1.63's validator *had* and this
one dropped. **A hash guards the body and says nothing about the fields beside
it.** Repaired, with two further frozen-document cases added.

A second probe case was itself defective: it substituted a literal that does not
appear in the approved body, so it mutated nothing and reported an escape from a
gate that was working. **A probe case that changes nothing tests nothing.**

## 7. Both apparatuses are blocked on the same kind of thing

```
anchor     6 unpublished operational questions
candidate  3 unpublished operational questions
```

All nine are methodology questions and none asks for data. That is one instrument
asked twice rather than two different problems.

The candidate's three are recorded as **questions** rather than as gaps, because
that is the shape they are now in:

1. Does each scan create a new document, or is a service document updated in place?
2. What is the membership of the datascan port set, and is TCP/22 in it?
3. Which fields are removed after thirty days, and are the address, the observation
   timestamp and the scanner node fields among them?

No second enquiry was drafted. Producing a second frozen document to sit beside an
undispatched one would add a hash and no progress.

## 8. Registry unchanged at 14

This mission demonstrates a rule — that an approval names a document and a
recipient must live outside the hashed range. It is not added, because it is a
property of **approval artifacts** and the requirement registry is the
**apparatus** registry.

## 9. What did not happen

```
measurement queries   0    trials         0    credentials written  0
target counts         0    purchases      0    webmail scraped      no
host records          0    facets         0    browser automated    no
banners               0    downloads      0    enquiries sent       0
first-party retrievals 7 across three targets
```

0 canonical mutations, 0 sources registered, 0 governance reviews, 0 Claims, 0
Evidence, 0 reliability values, 0 independence groups, 0 Scores, 0 model calls, 0
embeddings. Qualified apparatuses **0 of 4**, so `PAIR_ANALYSIS_NOT_READY`, and no
pair gate was evaluated.

## 10. Verification

| | |
|---|---|
| CI gates | 32, all green |
| bare-python | 1769 tests across 9 packages |
| pytest | 3310 tests, all suites passed, database unchanged |
| validator probe | 98 deliberate violations, 98 caught |
| approved enquiry hash after all 32 gates ran | unchanged |

Three probe cases edited the approved document and all three were caught.

**A pytest guard from Mission 1.23 caught this mission's prose**, and it was fixed
rather than exempted. That guard refuses any document outside a small allowlist
from containing the phrase reserved for the model-egress boundary. A sentence here
used it for outbound *email* — and, being a token scan, the guard cannot see that
the sentence was a denial. The wording was changed so the phrase stays reserved
for the boundary it governs, which is what makes a reserved-vocabulary scan worth
having. Widening the allowlist would have removed a guard to let new work through.

## 11. Next

**`STOP_ON_CONTACT_CHANNEL`.** The single blocking input is the exact first-party
contact address displayed on the anchor's published legal page.

To supply it: open <https://netlas.io/legal/> in a browser, where the obfuscated
address renders, and give the exact displayed string. The dispatch packet is
already generated from the frozen enquiry and needs only that line filled in.

```
APPROVE MISSION 1.61 ENQUIRY 310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4
```

And one decision beside it: whether a second enquiry should be drafted to the
candidate carrying its three residual questions, on the same frozen-and-approved
pattern.
