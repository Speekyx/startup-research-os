# TED-EU Database-Right Clarification Request V1

**Prepared, not sent.** Mission 1.15.3 §18–§21.

This document holds a ready-to-send clarification request for the Publications
Office. **Nothing has been transmitted.** No mail connector was used, no `sent_at`
is recorded, and sending it is an operator action.

**Status:** `PREPARED — AWAITING OPERATOR SEND`

---

## 1. Contact route

| | |
|---|---|
| **Primary recipient** | `op-copyright@publications.europa.eu` |
| **Basis** | The TED and SIMAP legal notice: *"For all other copyright issues regarding SIMAP, please contact: op-copyright@publications.europa.eu."* |
| **Secondary recipient (CSV subset question only)** | `GROW-D2@ec.europa.eu` |
| **Basis** | The `ted-csv` dataset description on data.europa.eu invites reusers to contact DG GROW unit D2 about reuse of that data |
| **Fallback** | TED helpdesk, `https://ted.europa.eu/en/contact` |

Both addresses are published by the operator in its own first-party material.
Neither was found through a search engine or a third party.

**Send to the primary address.** The secondary is only needed if question 4 goes
unanswered, because it concerns a dataset DG GROW publishes rather than one the
Publications Office publishes.

## 2. Subject line

```text
TED reuse: does the Publications Office assert a sui generis database right over the TED notice corpus?
```

## 3. The message

> Dear Publications Office,
>
> We operate **Startup Research OS**, a small evidence-based research tool that
> analyses published public-sector data to identify market opportunities. We are
> preparing to reuse TED procurement notices and want to confirm the legal basis
> before we collect anything. **We have collected no TED data.**
>
> **What we would do with the data.** Retrieve published contract notices and
> contract award notices; store them; extract a small set of structured fields;
> and compute aggregate statistics (for example, how procurement spending in a
> sector changes over time) that we would publish as commercial analytical
> research. Machine processing would be limited to inference, extraction,
> classification and structured analysis. **We would not train machine-learning
> models on TED data**, and we would not redistribute the notices or any
> substantial part of the corpus.
>
> **The fields we need.** Notice identifier, award value, currency, buyer
> organisation name, supplier organisation name, CPV classification, and the
> notice and award dates.
>
> **The fields we would discard.** All natural-person contact data — personal
> names, email addresses, telephone and fax numbers, and postal addresses. We
> would drop the entire contact block at the point of normalisation and never
> store it.
>
> **Access route.** Either the daily and monthly XML packages at
> `https://ted.europa.eu/en/simap/xml-bulk-download`, or the TED Search API at
> `https://api.ted.europa.eu/`. We have not decided between them and would like
> to know whether the answer differs.
>
> **What we have already established.** We have read Commission Decision
> 2011/833/EU in full. We understand from Article 3(2), Article 4 and Article 6
> that reuse is defined by purpose rather than by method, and that the commercial
> analytical reuse and the machine processing described above therefore fall
> inside the reuse grant. We also understand that the data.europa.eu record for
> the TED dataset (`ted-1`) declares `dct:license = COM_REUSE` on every
> distribution including the bulk download, and that the COM_REUSE authority
> concept carries `skos:exactMatch` to that Decision.
>
> **What we could not establish, and are asking about.** The Decision does not
> mention the sui generis database right, Directive 96/9/EC, extraction or
> re-utilisation, and neither does the TED legal notice, the Publications Office
> copyright notice or the TED API documentation. Our questions are:
>
> 1. **Does the European Commission or the Publications Office assert a sui
>    generis database right, or any other database-level right, over the
>    collection of TED procurement notices?**
>
> 2. **If so, does the reuse policy implemented by Commission Decision
>    2011/833/EU — as reflected in the `COM_REUSE` licence declared on the TED
>    dataset — authorise the repeated extraction and re-utilisation of
>    substantial parts of that collection for commercial analytical services,
>    including automated machine processing?**
>
> 3. **Does the answer differ between (a) the daily and monthly bulk XML packages
>    and (b) bounded use of the TED Search API?** We ask because the API's own
>    documentation describes a scroll mode with no limit on the number of
>    retrievable notices, so the two routes may not be as different in practice
>    as they look.
>
> 4. **Is the licensing difference in the data.europa.eu catalogue intentional?**
>    Twelve distributions of the `ted-csv` dataset declare CC BY 4.0 — whose
>    Section 4 expressly grants extraction and re-utilisation of a substantial
>    portion of a database — while thirty-six others, and every distribution of
>    `ted-1`, declare `COM_REUSE`. Some of these overlap in coverage:
>    `ted-contract-award-notices-2017-2021.zip` is CC BY 4.0 while
>    `ted-contract-award-notices-2018-2023.zip` is `COM_REUSE`. We do not want to
>    rely on whichever licence happens to be more favourable, so we would rather
>    ask.
>
> 5. **What does "the SIMAP's system metadata is dedicated to the public domain
>    in accordance with CC0 1.0" cover?** Specifically, does it extend to the
>    structured fields of published notices, or only to metadata about the SIMAP
>    system itself?
>
> A short written answer to questions 1 and 2 would be enough for us to proceed
> or to stop. We are happy to receive it in any form you find convenient.
>
> Thank you for your time.
>
> *[operator name and contact]*

## 4. Supporting identifiers to include if asked

| Item | Identifier |
|---|---|
| Governing Decision | Commission Decision 2011/833/EU · CELEX `32011D0833` · ELI `dec/2011/833/oj` · OJ L 330, 14.12.2011, pp. 39–42 |
| Licence concept | `http://publications.europa.eu/resource/authority/licence/COM_REUSE` |
| TED dataset record | `http://data.europa.eu/88u/dataset/ted-1` |
| CSV subset record | `http://data.europa.eu/88u/dataset/ted-csv` |
| Bulk route | `https://ted.europa.eu/en/simap/xml-bulk-download` |
| API specification | `https://ted.europa.eu/docs/v3` |
| Database directive | Directive 96/9/EC · CELEX `31996L0009` |

## 5. Required content checklist (§18)

| # | Requirement | Where |
|---|---|---|
| 1 | Brief identity of Startup Research OS | §3, opening paragraph |
| 2 | Exact intended use | §3, "What we would do with the data" |
| 3 | Exact data fields required | §3, "The fields we need" |
| 4 | Explicit personal-data minimisation | §3, "The fields we would discard" |
| 5 | Exact access route under consideration | §3, "Access route" |
| 6 | Decision 2011/833/EU findings | §3, "What we have already established" |
| 7 | H-34 CLOSED status | §3, same paragraph, stated as the reuse conclusion rather than by internal reference |
| 8 | Exact H-36 question | §3, questions 1 and 2 |
| 9 | Model training not part of current use | §3, "We would not train machine-learning models on TED data" |
| 10 | Natural-person contact data discarded | §3, "The fields we would discard" |
| 11 | Request for a written first-party answer | §3, closing paragraph |

Questions 3, 4 and 5 go beyond the required set. Question 3 is §20's bulk-versus-API
split. Questions 4 and 5 exist because this mission found two specific
ambiguities a person can resolve in a sentence, and asking is cheaper than
guessing.

## 6. Rules this document observes

- **Nothing was sent, and nothing claims to have been.** There is no `sent_at`
  field anywhere in this repository for it.
- **Both addresses are first-party**, published by the operator in its own legal
  notice and dataset description.
- **The request states our use accurately and does not narrow it to obtain a
  favourable answer.** Commercial analytical reuse, automated processing and
  storage are all named. Narrowing the described product to secure a permission
  would be a permission for a product we are not building.
- **It concedes what we already believe is settled** (the reuse grant covers our
  processing) rather than re-asking it, so the recipient's effort goes to the
  one question we cannot answer.
- **A "no" is a usable answer.** If the Publications Office asserts a database
  right and does not license it, TED becomes `RESTRICTED` and the portfolio moves
  to USAspending. That outcome is recorded in advance so the request is not
  written as advocacy.
