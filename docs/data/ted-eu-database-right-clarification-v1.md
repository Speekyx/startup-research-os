# TED-EU Database-Right Clarification V1 — the dataset licence, found and identified

**Authoritative.** Mission 1.15.3. What the first-party dataset-level material
says about the sui generis database right, and what it leaves open.

**H-36 does not close. It becomes answerable by a person.**

The licence attached to the assembled TED dataset **exists**, is
machine-readable, and **resolves to Commission Decision 2011/833/EU** — the
instrument Mission 1.15.2 read in full and found silent on database rights. Both
access routes are governed by that same silence.

**TED stays `REQUIRES_REVIEW`** at review v4. See
`ted-eu-database-right-clarification-request-v1.md` and
`ted-eu-h36-legal-review-packet-v1.md`.

---

## 0. What this mission was for

Mission 1.15.2 ended with *"the governing instrument does not address database
rights"*. That is a statement about **one document**. It leaves open the obvious
next question, which is the one §5 of this mission poses:

> Is there a licence attached to the **assembled dataset**, as opposed to the
> individual documents?

**There is.** Finding it is the substance of this mission, and it does not
produce the answer one might hope for.

## 1. The licence on the bulk route

The Publications Office publishes TED in its own open-data catalogue. The
DCAT-AP record is machine-readable and first-party:

```text
https://data.europa.eu/api/hub/repo/datasets/ted-1.rdf
```

| Property | Value |
|----------|-------|
| `dct:publisher` | `corporate-body/PUBL` — **Publications Office of the European Union** |
| `dct:creator` | **absent** |
| `dct:accessRights` | `access-right/PUBLIC` |
| `dct:license` **on the dataset node** | **absent** |
| `dct:rights` | **absent** |

Four distributions, and **every one carries a licence**:

| Distribution | Type | `dct:license` |
|---|---|---|
| Procurement notices by place of performance | WEB_SERVICE | `COM_REUSE` |
| Procurement notices by business sector | WEB_SERVICE | `COM_REUSE` |
| Procurement notices by type of business opportunity | WEB_SERVICE | `COM_REUSE` |
| **Last daily editions of procurement notices in bulk download** | **DOWNLOADABLE_FILE** | **`COM_REUSE`** |

The fourth is the bulk route, `accessURL` pointing at
`https://ted.europa.eu/en/simap/xml-bulk-download`. Cross-confirmed through the
portal's JSON record, which returns `license: null` at dataset level and
`COM_REUSE` on each distribution.

**So a licence is attached to the bulk route.** The question is what it says.

## 2. What COM_REUSE is

Resolved from the Publications Office's own authority table:

```text
http://publications.europa.eu/resource/authority/licence/COM_REUSE
```

| | |
|---|---|
| `skos:prefLabel` | European Commission reuse notice |
| **`skos:exactMatch`** | **`http://data.europa.eu/eli/dec/2011/833/oj`** |
| `eli:responsibility_of_agent` | `corporate-body/COM` |
| `cc:requires` | `cc:Attribution` |
| `euvoc:appliesTo` | `licence-domain/DATA`, `licence-domain/W_LIT_ART` |

**`skos:exactMatch` is the whole finding.** The publisher's own metadata asserts
that the licence on the bulk download **is** Commission Decision 2011/833/EU.

Which means the chain closes, documentarily, on a document already read:

```text
data.europa.eu ted-1  →  bulk XML distribution  →  dct:license COM_REUSE
                                                        ↓ skos:exactMatch
                                          Decision 2011/833/EU
                                          — zero occurrences of "sui generis",
                                            "extraction", "re-utilisation",
                                            Directive 96/9/EC
```

The definition text adds nothing new: reuse authorised provided the source is
acknowledged, conditions may be specified in individual copyright notices, reuse
not applicable to third-party IP.

### The appliesTo trap

`euvoc:appliesTo licence-domain/DATA` is the most tempting over-read available
here, and it is wrong. The `DATA` concept is defined in the same authority table
as:

> *"Set of values of qualitative or quantitative variables"*

That is a **subject-matter class, not a class of right**. It says the licence may
be applied to data as well as to literary and artistic works. It says nothing
about rights in a *collection*.

And the vocabulary offers no way to say otherwise: the whole `licence-domain`
scheme is `CODE`, `DATA`, `METADATA`, `W_LIT_ART` and a placeholder. **There is
no `DATABASE` domain.** So the absence of a database-right claim in COM_REUSE is
not evidence of a deliberate choice either — the vocabulary could not have
expressed one. `CC_BY_4_0` carries the *same two* `appliesTo` values.

## 3. The API route is governed by the same document

The TED Search API serves its own OpenAPI 3.1.0 specification at
`https://ted.europa.eu/docs/v3`. Its `info.description` contains a section headed
**Terms of Usage**, and that section's entire content is one link:

```text
<li><a href="https://ted.europa.eu/en/legal-notice">Legal notice</a></li>
```

The introduction says the API *"is accessible to the general public and can be
utilized by anyone in accordance with the term of usage"*.

**Bulk XML and the search API are governed by the same instrument**, and it is
the one that does not mention the right. The specification contains no occurrence
of `sui generis`, `database`, `extraction`, `re-utilisation`, `licence` or
`copyright`.

## 4. The exact subject of every licence

§5, §6 and §7 require the subject of each licence be recorded exactly. From the
TED legal notice, verbatim:

| Licence | Exact subject |
|---------|---------------|
| Decision 2011/833/EU | *"the **procurement notices** published in the Supplement to the Official Journal of the European Union can be freely reused, for commercial or non-commercial purposes"* |
| **CC BY 4.0** | *"The copyright over **the editorial content of the SIMAP websites** (TED, TED eNotices2, TED Developer Docs and TED Developer Portal)"* |
| **CC0 1.0** | *"The **SIMAP's system metadata** is dedicated to the public domain"* |

**CC BY 4.0 on the TED legal notice covers website editorial content.** Not the
notices, not the dataset, not the database. §7 answered.

**CC0 1.0 covers system metadata.** §6 answered, and the boundary Mission 1.15.2
drew holds.

One honest caveat, which becomes a question rather than a finding: **the page
nowhere defines "system metadata"**. If it were read as covering the structured
fields of the notices — buyer, supplier, value, CPV, dates — then CC0 would waive
sui generis rights over precisely the fields the engine wants. That reading is
not supported by anything on the page, so it is not adopted. It is asked.

## 5. The sharpest fact this mission found

**The same portal declares CC BY 4.0 on TED data — under a different publisher,
on a different dataset, inconsistently.**

`ted-csv` is *"Tenders Electronic Daily (TED) (csv subset)"*, published by
`corporate-body/GROW` (DG GROW), covering 2006-01-01 to 2023-12-31, carrying
*"the most important fields from the contract notice and contract award notice
standard forms, such as who bought what from whom, for how much"*.

Of its **48 distributions: 36 declare `COM_REUSE`, 12 declare `CC_BY_4_0`.**

| CC BY 4.0 (12) | |
|---|---|
| contract **award** notices | 2013, 2017-2021, 2018-2022, 2020, 2021, 2022 |
| contract notices | 2012, 2017-2021, 2018-2022, 2020, 2021, 2022 |

### Why this matters

CC BY 4.0 addresses the right COM_REUSE does not. From the licence's own text:

- **Section 1**: *"Sui Generis Database Rights means rights other than copyright
  resulting from Directive 96/9/EC … as amended and/or succeeded, as well as
  other essentially equivalent rights anywhere in the world."*
- **Section 4**: *"for the avoidance of doubt, Section 2(a)(1) grants You the
  right to extract, reuse, reproduce, and Share all or a substantial portion of
  the contents of the database"*.

So a `dct:license` field on TED-derived data **does** sometimes name a licence
that reaches this right.

### Why it is not relied on

Two reasons, and both are load-bearing:

1. **Those files are not the corpus.** They are a DG GROW CSV subset, a separate
   dataset with a separate publisher. Nothing on `ted-1` carries CC BY 4.0. A
   licence on twelve zip files licences twelve zip files.
2. **The assignment is internally inconsistent.**

   | File | Licence |
   |---|---|
   | `ted-contract-award-notices-2017-2021.zip` | **CC BY 4.0** |
   | `ted-contract-award-notices-2018-2023.zip` | **COM_REUSE** |

   Award notices for **2018 to 2021 sit under both licences**, depending on which
   zip is downloaded. The same holds for contract notices, and for 2020 data
   (`ted-contract-award-notices-2011-2020.zip` is COM_REUSE while
   `ted-contract-award-notices-2020.zip` is CC BY 4.0).

**Selecting the favourable licence would be selecting a licence by selecting a
filename.** That is not a rights basis. It is, however, an excellent question:
*is the difference deliberate?* A person at the Publications Office or DG GROW
can answer it in one sentence, and this mission's clarification request asks it.

## 6. Where else the right could have been addressed, and was not

| Document | Occurrences of *sui generis* / *database right* / *extraction* / *re-utilisation* / 96/9 |
|---|---:|
| TED and SIMAP legal notice | **0** |
| Publications Office copyright notice | **0** |
| europa.eu legal notice | **0** |
| data.europa.eu legal notice (20,015 chars) | **0** |
| TED XML bulk download page | **0** |
| TED Search API OpenAPI specification | **0** |
| `ted-1` DCAT record (all fields) | **0** |
| Commission Decision 2011/833/EU (Mission 1.15.2) | **0** |
| HTTP response headers on the packages | **0** |

The Publications Office's own notice defers explicitly: *"If you would like to
reuse specific content available on the websites EUR-Lex, European Data, EU
Tenders or CORDIS, please consult their respective copyright notices"* — back to
TED's, which defers to the Decision.

**The chain is complete and it closes without ever mentioning the right.**

## 7. Directive 96/9/EC — enough to make the question precise

Retrieved first-party from the Publications Office Cellar (CELEX `31996L0009`,
Cellar `b48976b5-b31a-4dba-a052-87133e17d65e`, 35,098 characters). Read only far
enough to state H-36 in the instrument's own terms, per §11 — **this is not a
legal opinion**.

- **Article 7(1)** — the right belongs to *"the **maker** of a database which
  shows that there has been qualitatively and/or quantitatively a **substantial
  investment** in either the obtaining, verification or presentation of the
  contents"*, to prevent extraction and/or re-utilisation of *"the whole or of a
  substantial part"*.
- **Article 7(2)(a)** — *"'extraction' shall mean the permanent or temporary
  transfer of all or a substantial part of the contents of a database to another
  medium by any means or in any form"*. **This is what a collector does.**
- **Article 7(2)(b)** — *"'re-utilization' shall mean any form of making
  available to the public all or a substantial part of the contents"*. The engine
  publishes derived claims, not the corpus, so this limb is less directly
  engaged than the first.
- **Article 7(3)** — the right *"may be transferred, assigned or granted under
  contractual licence"*. **A licence can carry it. COM_REUSE does not.**
- **Article 7(5)** — *"The repeated and systematic extraction and/or
  re-utilization of **insubstantial** parts … implying acts which conflict with a
  normal exploitation of that database"* is not permitted. **This reaches the API
  route even if each query is small.**
- **Article 8(1)** — a lawful user may not be prevented from extracting
  insubstantial parts *"for any purposes whatsoever"*.
- **Article 11** — subsistence depends on the maker's nationality or
  establishment.

## 8. H-36A and H-36B, separately

### H-36A — does a sui generis right subsist?

**NOT ESTABLISHED, in either direction.**

Article 7(1) makes subsistence turn on a **maker** and a **substantial
investment**, and no first-party document retrieved states either. The `ted-1`
record names a `dct:publisher` and carries **no `dct:creator` at all**. Notices
are filed by contracting authorities across the Union; who assembled the
collection in the Article 7(1) sense is a question the catalogue does not answer,
and Article 11 then makes subsistence depend on facts about that maker.

**This is a legal question about facts nobody has published, not a retrieval
gap.** §10 forbids concluding it from architecture, and nothing here does.

### H-36B — does the right holder grant or waive?

**NOT ADDRESSED for either route.**

The licence on every `ted-1` distribution including bulk XML is COM_REUSE, which
**is** the Decision, which has no database-right provision. The API's Terms of
Usage resolve to the same TED legal notice. Article 7(3) shows a licence *can*
carry the right; these do not.

The CC BY 4.0 files in `ted-csv` show the same publisher's catalogue sometimes
naming a licence that *does* — inconsistently, on a different dataset, over
overlapping coverage.

## 9. The two routes

| | Bulk XML | Search API |
|---|---|---|
| Governing terms | `COM_REUSE` → Decision 2011/833/EU | Terms of Usage → TED legal notice |
| Database-right provision | **none** | **none** |
| Authentication | none (HEAD returns 200) | none for published notices |
| Documented volume limits | none | 15k notices per query (pagination); **no limit on retrievable notices (scroll)** |
| One request transfers | 16.7 MB daily / **427 MB monthly** | up to 250 notices per page, unbounded pages in scroll mode |
| H-36 status | **unresolved** | **unresolved** |

### A correction to Mission 1.15.2

That review reasoned the API was *"less obviously a substantial part, and
correspondingly less exposed"*. Two facts found here weaken that:

1. The API's own specification documents a **scroll mode with no limit on the
   number of retrievable notices** — bulk-equivalent by design.
2. **Article 7(5)** reaches repeated and systematic extraction of *insubstantial*
   parts regardless of per-request size.

Both routes stay analysed separately and both stay unresolved. The gap between
them is smaller than v3 recorded, and **no collector route is preferred on that
basis** — which was the point of not forcing one.

## 10. What technical provision does not establish

Recorded because the temptation is strong and §13 and §15 both name it.

The Publications Office **publishes** the packages without sign-in, **documents**
a scroll mode with no notice limit, and **writes**, in its own developer
documentation, that the API lets developers *"Retrieve published procurement
notices from the TED website for analysis or reuse"* and that the Search API
*"allows access to these notices for reuse or analysis"*, naming *"reusers of TED
Data"* as an audience.

That is an invitation to reuse. **It is not a grant of a right in the
collection**, and no amount of it becomes one.

## 11. Open-data framework (§12)

**No documentary chain exists.**

Directive (EU) 2019/1024 appears in **none** of the notices, the catalogue
records, the API specification or the Decision. The single occurrence of
Directive 2003/98/EC across everything retrieved is inside the **data.europa.eu
privacy statement**, cited as a legal basis for processing personal data in
operating the portal — not as a reuse-rights chain for TED content.

Recorded as separate legal context, not controlling evidence.

## 12. What would close H-36

In order of cost, unchanged in shape from Mission 1.15.2 but now with a named
addressee and a precise question:

1. **A written first-party answer** from the Publications Office at
   `op-copyright@publications.europa.eu`, the address its own legal notice
   publishes for copyright issues regarding SIMAP. DG GROW's `GROW-D2@ec.europa.eu`
   is the corresponding route for the CSV subset question. See
   `ted-eu-database-right-clarification-request-v1.md`.
2. **Legal review** of whether the sui generis right subsists in TED given who
   assembles it, and whether a documents reuse policy carries it by implication.
   See `ted-eu-h36-legal-review-packet-v1.md`.

**Neither is engineering work, and no further document search will settle it.**
The documents have been read, the catalogue has been read, the metadata has been
read, and the headers have been read.

## 13. What was not done

No procurement notice was fetched. HEAD requests returned headers and no package
body. Whether a licence or README travels **inside** the archives could only be
established by downloading procurement content, which §4 forbids — **that limit
is recorded rather than worked around**, which is the outcome §4 asks for.
