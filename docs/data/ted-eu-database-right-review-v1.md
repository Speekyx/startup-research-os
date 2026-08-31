# TED-EU Database-Right Review V1 — H-36 Not Closed

**Authoritative.** Mission 1.15.2 §15. Whether the reuse framework reaches the
sui generis database right.

**H-36 does not close.** Outcome C — the governing instrument was read in full
and does not address database rights at all. This is now the **only** question
standing between TED and an approving verdict.

---

## 0. Why this is a separate question

Mission 1.15.1 raised H-36 and Mission 1.15.2 was required not to close H-34 and
stop (§15). The reason is structural:

```text
copyright in a document        governs copying and adapting THAT DOCUMENT
sui generis database right     governs extracting and re-utilising substantial
                               parts of THE COLLECTION the documents sit in
```

They are different rights with different holders, different terms and different
tests. **A grant over documents does not carry a right in the database by
implication**, and the second is the one that bites on bulk extraction.

TED's documented reuse route is *daily and monthly bulk XML packages*. That is
extraction and re-utilisation of substantial portions of a collection, which is
precisely the activity the second right addresses.

## 1. What the Decision says about it

**Nothing.** Read in full — 16,748 characters, Articles 1–13 with recitals — and
searched term by term:

| Term | Occurrences |
|------|------------:|
| `sui generis` | **0** |
| `extraction` | **0** |
| `re-utilisation` / `reutilisation` | **0** |
| `Directive 96/9` / `96/9` | **0** |
| `text and data mining` / `mining` | **0** |
| `database` | 2 — **neither relevant** |

The two occurrences of *database*:

1. **Article 2(2)(e)**, excluding *"documents resulting from ongoing research
   projects conducted by the staff of the Commission which are not published or
   available in a published database"* — an exclusion criterion, not a rights
   statement.
2. **Article 3(6)**, defining structured data as *"data organised in a way that
   allows reliable identification of individual statements of fact and all their
   components, as exemplified in databases and spreadsheets"* — an example
   inside a definition.

Neither says anything about rights in a database.

## 2. What the Decision governs instead

**Article 1:** the conditions for the reuse of **documents** held by the
Commission or the Publications Office.

**Article 2(1):** it applies to public **documents** produced by or for the
Commission and published through publications, websites or dissemination tools.

**Article 3(1):** a document is *"any content whatever its medium"* and *"any
part of such content"*.

The instrument is framed, consistently and throughout, around **documents**. The
collection those documents sit in — its structure, its selection, the investment
in obtaining and presenting it — is never mentioned.

**Article 2(2)(a)** excludes documents covered by industrial property rights
*"such as patents, trademarks, registered designs, logos and names"*. The
database right is not in that list, and is not elsewhere either. So the Decision
neither grants over it nor excludes it: **it does not reach it.**

## 3. Where else it might have been addressed, and was not

| Document | On database rights |
|----------|--------------------|
| TED and SIMAP legal notice | Silent. Grants reuse of *notices*; licenses editorial content CC BY 4.0 and metadata CC0 1.0 |
| Publications Office copyright notice | Silent |
| TED Developer Docs | Silent; carries no licence and links back to the legal notice |
| Commission Decision 2011/833/EU | Silent, established above |

**One observation cuts the other way and is recorded honestly**: SIMAP *system
metadata* is dedicated to the public domain under CC0 1.0. That is a first-party
waiver over metadata, and CC0 waives sui generis database rights where the
dedicator holds them. It is evidence that the Publications Office knows how to
address this class of right when it means to — and it applies to *metadata*,
which is not the notice corpus a collector would extract.

Reading that waiver as covering the notices would be extending a stated grant
past its stated subject, which is the same error as reading a documents grant
onto a database.

## 4. Why silence cannot be read as permission here

The argument for closing H-36 favourably goes: the Publications Office publishes
bulk packages for download without sign-in, tells reusers to take them, and
declares the documents freely reusable — so whatever rights it holds must be
effectively licensed.

That is a plausible legal *inference*. It is not a documented grant, and §15
requires first-party material. Three specific reasons not to make it:

1. **The maker of the database may not be the Commission alone.** Notices are
   filed by contracting authorities across the Union. Who holds a right in the
   assembled collection is not established by anything retrieved.
2. **The Decision distinguishes carefully elsewhere.** It excludes third-party
   IP (Article 2(2)(b)) and industrial property (2(2)(a)) by name. An instrument
   that enumerates rights it cannot grant over is not one whose silence should be
   read as a grant.
3. **The engine's access route is the aggravating case, not the mild one.**
   Bulk daily and monthly packages are the paradigm of repeated and systematic
   extraction of substantial parts. If any use engages the right, this one does.

## 5. Bulk and search API may differ (§29)

Analysed separately, because they may not share an answer:

| Route | Position |
|-------|----------|
| **Bulk XML packages** | The documented reuse route, published for download without sign-in. Also the clearest case of extracting substantial portions. **Unresolved, and it is the route a collector would want.** |
| **Read-only search API** | Returns individual notices matching a query. Less obviously a substantial part of the collection, and correspondingly less exposed — but no first-party document addresses it either, so it is unresolved on the same evidence |

**Neither is authorised. Neither is prohibited.** The mission's §29 explicitly
permits a split outcome, and the honest state today is that both are unresolved
for the same reason, with different risk profiles if the question is ever
answered adversely.

**No collector route was forced.** Choosing bulk now because it is convenient
would be choosing the more exposed route before knowing whether the exposure is
real.

## 6. H-36's state

**Outcome C — NOT_ADDRESSED / legal review required.**

The distinction from Mission 1.15.1's position is worth stating: this is no
longer *"the instrument might address it and we cannot read the instrument"*. The
instrument has been read in full and **does not address it**. That converts an
unknown into an established absence, which is what makes the next step a legal
question rather than another retrieval.

## 7. What would close it

In increasing order of cost:

1. **A first-party statement from the Publications Office** on whether it
   asserts or waives database rights in TED, or whether the reuse policy is
   intended to cover extraction of the corpus. The Publications Office publishes
   a contact route.
2. **A licence attached to the bulk packages themselves**, if one exists and was
   not found — the data-reuse page carries none.
3. **Legal review** of whether a documents reuse policy carries the database
   right by implication under EU law, and whether the sui generis right subsists
   in TED at all given who assembles it.

The third is a real legal question and not a retrieval. **It is the appropriate
next action and it is not engineering work.**

## 8. Consequence for the verdict

Per §24: H-34 permitted with H-36 unresolved gives **`REQUIRES_REVIEW`**.

All six load-bearing activities are now positively granted and TED is still
blocked. That is uncomfortable and correct — the remaining question is not an
activity in the matrix, it is whether a different body of rights sits over the
same data.

**A favourable H-34 must not be allowed to overwrite an unresolved H-36** (§23),
and the shape of this outcome is exactly why the mission said so.
