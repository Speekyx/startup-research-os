# TED-EU Reuse and Machine-Learning Processing Review V1

**Authoritative.** Mission 1.15.1. The narrow review of H-34.

**Outcome C — H-34 remains OPEN.** TED-EU stays `REQUIRES_REVIEW` at review v2.
No activity assessment changed. What changed is that the governing instrument is
now named and proven to apply, its text could not be retrieved, and a second
question surfaced that nobody had asked.

---

## 0. The question

Mission 1.15 recorded seven of TED's activity assessments as `PERMITTED` on one
retrieved sentence, and one as `NOT_ADDRESSED`:

> H-34 — does the Publications Office's reuse decision, or another first-party
> instrument, address machine-learning processing of reused notices?

That single `NOT_ADDRESSED` is the whole distance between TED and an approving
verdict, and TED would be the portfolio's first transaction-class source. This
mission existed to answer it, in either direction.

**It could not be answered.** The reason is worth reading, because it is not the
reason anybody expected.

## 1. The governing instrument — established

Mission 1.15 guessed. This round proved it, from TED's own legal notice:

> *"The European Commission's reuse policy is implemented by the Commission
> Decision of 12 December 2011 on the reuse of Commission documents."*

with a link to `https://eur-lex.europa.eu/eli/dec/2011/833/oj`.

| | |
|---|---|
| **Document** | Commission Decision 2011/833/EU of 12 December 2011 on the reuse of Commission documents |
| **Publisher** | European Commission; published in Official Journal L 330 |
| **Canonical URL** | `https://eur-lex.europa.eu/eli/dec/2011/833/oj` |
| **Relationship to TED** | Named by TED's own legal notice as the instrument implementing the reuse policy under which notices are reusable |
| **Retrieved** | **No — see §2** |

**The link is proven, not assumed.** §5 of the mission is explicit that a generic
EU open-data statement must not be presumed to govern TED. This is not a generic
statement: it is TED naming its own instrument.

The TED Developer Docs were also retrieved and carry no licence of their own,
linking back to the same legal notice — which establishes that the legal notice
is *the* governing statement on the TED side rather than one of several.

## 2. The retrieval failure

**Five first-party EUR-Lex addresses, all empty bodies, on 2026-08-31:**

| URL form | Outcome |
|----------|---------|
| `eur-lex.europa.eu/eli/dec/2011/833/oj` | Empty body |
| `eur-lex.europa.eu/eli/dec/2011/833/oj/eng` | Empty body |
| `eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32011D0833` | Empty body |
| `eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32011D0833` | Empty body |
| `eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=OJ:L:2011:330:0039:0042:EN:PDF` | Empty body |

Two further first-party routes were tried and neither restates the Decision:

- **Publications Office copyright notice** — the body that operates TED. Governs
  its website's publications under CC BY 4.0 and is **silent** on commercial
  reuse, databases, text and data mining, machine learning and automated
  processing.
- **`data.europa.eu/en/dataset-legal-notice`** — HTTP 404.

**No substitute was used.** No mirror, no cached copy, no archive, no
third-party transcription.

One case deserves naming because it was the direct temptation. A search restricted
to EU domains returned a summary that *described* the Decision's articles —
including apparent statements about what "reuse" means and about documents being
made available without restrictions. **That was not treated as evidence, and no
part of this review rests on it.** §4 is unambiguous: search-engine snippets are
not evidence. A summary of a legal instrument is precisely the thing that must
not stand in for the instrument.

## 3. Why this leaves H-34 open rather than closing it

The operative grant reads:

> *"the procurement notices published in the Supplement to the Official Journal
> of the European Union can be freely reused, for commercial or non-commercial
> purposes"*

Mission 1.15 §7 permits closing H-34 without the exact phrase "machine learning"
**if a broader legal permission clearly and explicitly covers the activity** —
and forbids inferring permission from silence.

The problem is narrower and worse than silence:

> **"reuse" is a defined term in an instrument that could not be read.**

The grant does not say "freely used". It says *reused*, and it says so while
naming the Decision that implements the reuse policy. The scope of the permission
is therefore whatever that Decision's definition makes it — which is exactly the
text that returned an empty body five times.

Reading the grant as covering machine-learning inference would mean assuming a
definition. That is not inferring permission from observed silence; it is
inferring permission from **an unread document**, which is worse, because silence
is at least a fact one has established.

**Nothing about this reasoning depends on which answer would be convenient.** If
the Decision's definition of reuse turns out to cover computational analysis,
H-34 closes as permitted on the next retrieval. If it excludes it, H-34 closes as
prohibited. The review has no stake in which.

## 4. What was NOT collapsed

§3 requires four activities to be kept apart. They are:

| Activity | Finding |
|----------|---------|
| **Machine-learning inference** | `NOT_ADDRESSED` — the H-34 question |
| **Embeddings** | `NOT_ADDRESSED`, and **not** treated as inheriting an inference decision. D-12 is open and nothing here was implemented |
| **Model training** | `NOT_ADDRESSED`. **Not part of the assessed need**: the engine needs inference, extraction and classification before it needs training, and §14 is explicit that training uncertainty must not block inference where the framework treats them separately |
| **Generative output** | Not assessed; not required by any current or planned stage |

No document retrieved this round addresses any of the four.

## 5. What surfaced that nobody had asked — database rights

**H-36, new.**

TED is a database. The documented reuse route is **bulk daily and monthly XML
packages**, which is extraction and re-utilisation of substantial portions of it.

The sui generis database right is independent of copyright. A reuse grant framed
around documents does not automatically carry it, and:

- the TED legal notice does not mention databases, extraction or re-utilisation;
- the Publications Office copyright notice does not either;
- the Decision that might address it could not be read.

Mission 1.15's review did not ask this. It is recorded as a new open question
rather than used to downgrade v1's findings, because **it is a question nobody
has answered rather than evidence that v1 was wrong** — and rewriting a prior
review on a suspicion is exactly what the append-only rule exists to prevent.

If the answer is that the grant does not reach the database right, it would bear
on `automated_access` (bulk) and `redistribution` more than on `model_processing`
— so H-36 could matter even if H-34 closes favourably.

## 6. Conditions — two added, three preserved

The re-read of the legal notice produced two obligations Mission 1.15's review
did not record. Both are recorded on v2 **in addition to** v1's three, none of
which was weakened:

**Preserved from v1:**

1. Attribution under CC BY 4.0 for reused editorial material, with changes
   indicated; the Publications Office logo requires prior consent.
2. **Personal-data minimisation.** Notices publish contact names, addresses,
   emails, telephone and fax numbers. The engine keeps the award value,
   currency, buyer and supplier organisation names, CPV classification, contract
   dates and notice id; it discards the entire contact block. **Unchanged, and
   not weakened** — H-34 concerns reuse and ML processing, never permission to
   ingest more personal data.
3. **Authenticity.** Only electronically signed notices in the Official Journal
   Supplement are authentic; online documents are *"not necessarily exact
   reproductions"*. Any future claim must be attributed to TED's published
   notice and must never silently assert it is the legally authentic contract.
   **Unchanged.**

**Added in v2:**

4. The notice states that additional rights may need clearing where content
   depicts identifiable private individuals or includes third-party works, and
   that content not owned by the EU may require the rightholder's permission.
   **The reuse grant is not a blanket grant over everything inside a notice**,
   which makes minimisation a compliance requirement rather than a preference.
5. Industrial property — patents, trademarks, registered designs, logos and
   names — is excluded from the reuse policy and not licensed. Supplier and
   buyer *names* appear in award notices as facts about a procurement; using
   them as trademarks is a different act and outside the grant.

## 7. Transaction semantics — recorded as a gap

§24 asks whether TED award data can distinguish an amount actually paid from
other monetary fields. **The documentation retrieved does not establish this**,
and no procurement data was fetched to check.

The distinctions that will matter, none of them yet evidenced:

```text
award value actually reported        estimated contract value
maximum framework value             listed budget
lot value                           currency and conversion
amendments and their effect on the original value
```

**Recorded as a gap, not flattened.** Treating every monetary field as "paid"
would be the LISTED_PRICE / TRANSACTION conflation that made TED worth
registering in the first place. Establishing the field semantics belongs to
whichever mission reads the schema — after permission exists, not before.

## 8. Willingness to pay — what TED could and could not support

Even fully permitted, TED would give **direct evidence that an organisation
awarded a procurement contract of a stated value to a stated supplier.**

It would **not** show that anyone is willing to pay for SaaS. A WTP-adjacent
proposition would need the procured category, the buyer, the supplier, the
contract's nature and the award value to make that reasoning defensible — and
each of those is a claim-layer question, governed by the interpretation contract,
for a mission that has permission and data.

The same caution applies to competition: named winning suppliers do not establish
market share or competitive position.

**No Claim of any kind was produced in this mission.**

## 9. Where this leaves TED

| | |
|---|---|
| Verdict | `REQUIRES_REVIEW` (unchanged) |
| Review version | **2** |
| H-34 | **OPEN**, refined |
| H-36 | **NEW** |
| Collector-eligible | No |
| `AcquisitionAuthorizationContext` | Cannot be built — the source does not pass the eligibility gate |
| Collector | Not implemented, and not permitted to be |

**The next action is one retrieval, from an environment that can render
EUR-Lex.** Commission Decision 2011/833/EU, Articles defining scope and reuse.
That is a smaller and more precise task than the one Mission 1.15 handed forward,
which is the only thing this mission improved — and it is a real improvement,
because "read this named document" is work somebody can do, and "find out what
governs this" was not.
