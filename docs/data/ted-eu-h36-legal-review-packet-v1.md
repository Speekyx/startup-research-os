# TED-EU H-36 Legal Review Packet V1

**For a lawyer or qualified reviewer.** Mission 1.15.3 §22.

**This document states established facts and asks a question. It contains no
legal conclusion, and the engineering team is not qualified to reach one.**

Everything below was retrieved first-party on 2026-08-31. Every URL is the
publisher's own. No mirror, archive, cache, search snippet, legal blog or
third-party database was used at any point across Missions 1.15 to 1.15.3.

---

## 0. The question

> **Does Startup Research OS have the right to extract and re-utilise TED
> procurement notice data as a database or collection — including repeated
> extraction of substantial parts — under the reuse framework the Publications
> Office applies to TED?**

Split, because the two halves need different work:

| | |
|---|---|
| **H-36A** | Does a sui generis database right (or equivalent) **subsist** in the TED notice corpus, and who would hold it? |
| **H-36B** | If it does, does the applicable right holder **grant or waive** extraction and re-utilisation for this use? |

## 1. What the intended use is

| | |
|---|---|
| **Access** | Daily/monthly XML packages, **or** the TED Search API. Not decided |
| **Volume** | Repeated, ongoing. One monthly package is ~427 MB |
| **Fields kept** | Notice id, award value, currency, buyer organisation name, supplier organisation name, CPV code, dates |
| **Fields discarded** | All natural-person contact data — names, email, telephone, fax, postal address. Dropped at normalisation, never stored |
| **Processing** | Inference, extraction, classification, structured analysis. **No model training. No embeddings** |
| **Output** | Aggregate derived statistics published as commercial analytical research. **The notices are not redistributed** |
| **Collected so far** | **Nothing.** Zero TED rows exist in any table |

## 2. The instruments, and what each one covers

### 2.1 Commission Decision 2011/833/EU

CELEX `32011D0833` · ELI `dec/2011/833/oj` · OJ L 330, 14.12.2011, pp. 39–42.
Retrieved in full from the Publications Office Cellar (identifier
`cb76d4a0-c886-40bd-99d7-8db018a723d0`), 4 pages, Articles 1–13.

| Article | Provision |
|---|---|
| 1 | Determines the conditions for reuse of documents held by the Commission **or on its behalf by the Publications Office** |
| 2(1) | Applies to public documents published through publications, websites or dissemination tools |
| 2(2) | Excludes: (a) software and industrial property; (b) documents covered by **third-party intellectual property rights**; (c) documents excluded from access under Reg. 1049/2001; (d) confidential data under Reg. 223/2009; (e) unpublished ongoing research |
| 2(4) | Nothing authorises reuse *"in a manner calculated to deceive or to defraud"* |
| 3(1) | A document is *"any content whatever its medium"* and *"any part of such content"* |
| **3(2)** | *"'reuse' means the use of documents … for commercial or non-commercial purposes **other than the initial purpose** for which the documents were produced"* |
| 4 | All documents available for reuse, commercially, without charge, without individual application |
| 6(1) | Available without restrictions, or under an open licence or disclaimer setting conditions |
| 6(2) | Conditions *"shall not unnecessarily restrict possibilities for reuse"*; may include attribution, **non-distortion**, non-liability |
| 11 | Non-discrimination between comparable categories of reuse; no exclusive rights |

**Term counts across the full text:** `sui generis` **0** · `extraction` **0** ·
`re-utilisation` **0** · `Directive 96/9` **0** · `database` **2** (an exclusion
for unpublished research at 2(2)(e); an example inside the definition of
*structured data* at 3(6)).

### 2.2 The licence declared on the TED dataset

`https://data.europa.eu/api/hub/repo/datasets/ted-1.rdf`

- `dct:publisher` = **Publications Office of the European Union**
- `dct:creator` = **absent**
- `dct:license` on the dataset node = **absent**; on **each of four
  distributions, including the bulk XML download** = `COM_REUSE`
- `http://publications.europa.eu/resource/authority/licence/COM_REUSE` carries
  **`skos:exactMatch` → `http://data.europa.eu/eli/dec/2011/833/oj`**

**The licence on the bulk route is, by the publisher's own machine-readable
assertion, the Decision above.**

### 2.3 The TED and SIMAP legal notice

`https://ted.europa.eu/en/legal-notice`. Three licences, three subjects, verbatim:

| Licence | Subject |
|---|---|
| Decision 2011/833/EU | *"the **procurement notices** published in the Supplement to the Official Journal"* |
| CC BY 4.0 | *"the **editorial content of the SIMAP websites**"* |
| CC0 1.0 | *"The **SIMAP's system metadata**"* — the term is nowhere defined |

Also: additional rights may need clearing where content depicts identifiable
private individuals or includes third-party works; industrial property is
excluded; logos require prior consent. Contact for copyright issues:
`op-copyright@publications.europa.eu`.

### 2.4 The API's terms

`https://ted.europa.eu/docs/v3` — the OpenAPI 3.1.0 document's **Terms of Usage**
section contains exactly one item, a link to the legal notice above. Documented
limits: pagination mode 15,000 retrievable notices per query, 250 per page,
10,000 fields per page; **scroll mode: no limit on the number of retrievable
notices**.

### 2.5 The enclosing notice chain

Publications Office copyright notice, europa.eu legal notice, data.europa.eu
legal notice. **None** contains `sui generis`, `database right`, `extraction`,
`re-utilisation`, Directive 96/9/EC or `data mining`. The Publications Office
notice defers reuse of *"EU Tenders"* content back to TED's own notice.

### 2.6 The CC BY 4.0 anomaly

`ted-csv` — a separate dataset, publisher **DG GROW**, coverage 2006–2023.
**48 distributions: 36 `COM_REUSE`, 12 `CC_BY_4_0`.** CC BY 4.0 Section 4
expressly grants the right *"to extract, reuse, reproduce, and Share all or a
substantial portion of the contents of the database"* where sui generis rights
apply; Section 1 defines them by reference to Directive 96/9/EC.

The assignment overlaps: `ted-contract-award-notices-2017-2021.zip` is CC BY 4.0
while `ted-contract-award-notices-2018-2023.zip` is `COM_REUSE`.

**Nothing on `ted-1` carries CC BY 4.0.**

### 2.7 Directive 96/9/EC

CELEX `31996L0009`, retrieved first-party from the Cellar (identifier
`b48976b5-b31a-4dba-a052-87133e17d65e`), 35,098 characters.

| Article | Provision, verbatim in the operative parts |
|---|---|
| 7(1) | Right for *"the **maker** of a database which shows that there has been qualitatively and/or quantitatively a **substantial investment** in either the obtaining, verification or presentation of the contents"* to prevent extraction and/or re-utilisation of *"the whole or of a **substantial part**"* |
| 7(2)(a) | *"'extraction' shall mean the permanent or temporary transfer of all or a substantial part of the contents of a database to another medium by any means or in any form"* |
| 7(2)(b) | *"'re-utilization' shall mean any form of **making available to the public** all or a substantial part of the contents"* |
| 7(3) | The right *"may be transferred, assigned or granted under contractual licence"* |
| 7(4) | Applies irrespective of copyright eligibility of the database or its contents |
| 7(5) | *"The **repeated and systematic** extraction and/or re-utilization of **insubstantial** parts … implying acts which conflict with a normal exploitation of that database or which unreasonably prejudice the legitimate interests of the maker"* is not permitted |
| 8(1) | A lawful user may not be prevented from extracting insubstantial parts *"for any purposes whatsoever"* |
| 11 | Subsistence turns on the maker's or rightholder's nationality, residence or establishment |

## 3. Facts bearing on H-36A

**For the reviewer to weigh. No conclusion is offered.**

| Fact | Source |
|---|---|
| TED is operated by the Publications Office; the site states *"This website is managed by: Publications Office of the European Union"* | ted.europa.eu |
| The catalogue names the Publications Office as **publisher** of `ted-1` and carries **no creator** | `ted-1.rdf` |
| Notices are filed with TED by **contracting authorities across the Union**, through eSenders and eNotices2 | TED Developer Docs |
| TED holds notices back to **1993** and publishes daily editions of the OJ Supplement | bulk download page |
| The Decision's own scope covers documents held by the Commission *"or on its behalf by the Publications Office"* | Art. 1 |
| No document retrieved asserts a substantial investment in obtaining, verification or presentation | — |
| No document retrieved identifies a database maker | — |

## 4. Facts bearing on H-36B

| Fact | Source |
|---|---|
| The licence on **every** `ted-1` distribution including bulk XML is `COM_REUSE` | `ted-1.rdf` |
| `COM_REUSE` is asserted **exactly equal** to Decision 2011/833/EU | authority table |
| That Decision contains no database-right provision | full text |
| The API's Terms of Usage resolve to the TED legal notice, which contains none either | OpenAPI spec |
| Art. 7(3) confirms such a right **can** be granted by contractual licence | Directive 96/9/EC |
| The same portal declares CC BY 4.0 — which **does** grant it — on 12 `ted-csv` distributions, inconsistently and on a different dataset | `ted-csv.rdf` |
| CC0 1.0 covers *"the SIMAP's system metadata"*, a term the notice does not define | legal notice |
| No PSI or open-data directive is incorporated by any TED or Publications Office reuse document | §11 of the clarification document |

## 5. What the reviewer is being asked

1. On the facts in §3, **does a sui generis database right subsist** in the TED
   notice corpus, and who would hold it?
2. If it does, **does a reuse policy framed around documents carry that right by
   implication**, or does its silence leave it reserved?
3. Does the answer differ between the **bulk packages** and the **search API**,
   given Article 7(5)?
4. Does the CC BY 4.0 designation on some `ted-csv` distributions constitute a
   grant over those specific files, notwithstanding the internal inconsistency?
5. Is the **CC0 1.0 dedication over "system metadata"** capable of covering the
   structured fields of published notices?

## 6. What is deliberately absent

- **No legal conclusion.** The engineering team stated the question and stopped.
- **No argument from public availability.** That the packages download without
  sign-in is recorded as a technical fact and treated as establishing nothing.
- **No argument from intent.** That the Publications Office documents the API for
  *"reusers of TED Data"* and invites reuse *"for analysis or reuse"* is recorded
  and is not treated as a rights grant.
- **No reliance on the favourable licence.** The CC BY 4.0 files are described in
  full, including the inconsistency that makes them unreliable.
- **No general legal knowledge presented as project evidence.** Directive 96/9/EC
  is quoted from its own retrieved text and used only to state the question in
  the instrument's own terms.

## 7. If the answer is unfavourable

TED becomes `RESTRICTED`, no technical workaround is pursued, and the
willingness-to-pay priority moves to `usaspending` (H-35). That is recorded here
so the packet reads as a question rather than as advocacy.
