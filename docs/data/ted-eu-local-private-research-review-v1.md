# TED-EU Local Private Research Review V1 — the official routes, and what they do and do not settle

**Authoritative.** Mission 1.15.4. A fresh first-party review of TED's two
official query routes against the system's **actual** current use.

**The routes' intended purpose is documented and it covers what we want to do.
The database-right question is untouched by that, and stays open.**

**TED remains `REQUIRES_REVIEW` at review v5.** No authorisation was created,
because the model cannot express one — see
`route-scoped-source-authorization-gap-v1.md`.

---

## 0. Why this review exists

Reviews v1 to v4 assessed a **demanding** use case, deliberately: commercial
multi-tenant SaaS, repeated collection at corpus scale, potentially substantial
dataset reuse, commercial analytics. That was the right thing to assess, because
a permission obtained by describing a smaller product is a permission for a
product we are not building.

The system's **actual current use** is narrower:

| | |
|---|---|
| Deployment | local |
| Users | one, the developer |
| Public access | no |
| External customers | no |
| Raw redistribution | no |
| Raw resale | no |
| Commercial service operating | no |
| Model training | no |
| Embeddings | no (D-12) |
| Analysis, extraction, classification | yes |
| Storage | minimised |

**This does not create permission.** §1 of the mission says so and it is worth
repeating in the document a future reader will find first: *"it is local,
therefore anything is allowed"* is not an argument, and nothing here rests on
it. Permission comes from the source.

What the narrower use changes is **which question is worth asking**. Not *may we
mirror the corpus commercially*, but *do the official query routes document a
purpose that covers narrow local research*.

## 1. What was excluded before anything else (§32)

A file at `C:\Users\Hp\Downloads\ted-eu-publications-office-response.txt`
describes a reply from the Publications Office. **It was excluded from all policy
reasoning.**

It is a user-written transcription, and it says so itself: *"This file is NOT a
verbatim copy of the original email"* and *"The response therefore confirms,
according to the user who received it, that repeated reuse is authorised."*

| | |
|---|---|
| Classification | `USER_SUPPLIED / NON_AUTHORITATIVE` |
| Cited as Publications Office evidence | **no** |
| Present in the repository | **no** — it lives outside the working tree and was not copied in |
| Present in the catalog as evidence | **no** — `OPERATOR_CORRESPONDENCE` rows for `ted-eu`: **zero** |
| Deleted | **no.** §32 says do not delete user data automatically |

The project's own rule already covered this before the mission restated it
(`source-review-guide.md`): *"Do not guess, and do not substitute a second-hand
description of it."* A test now asserts that no `OPERATOR_CORRESPONDENCE`
evidence exists for TED, so a summary cannot later be promoted into the registry
quietly.

**There is still no written response from the Publications Office. H-36 is
exactly where Mission 1.15.3 left it.**

## 2. The TED Search API — what the operator says it is for (§5)

`https://docs.ted.europa.eu/api/latest/search.html`, published by the
Publications Office.

> *"The Search API allows access to published procurement notices **for analysis
> and reuse**, promoting transparency."*

> *"The Search API provides access to published notices via expert queries and
> enables bulk downloads of notices in XML format **for reuse or analysis**. Note
> that this API is **primarily targeted at data reusers** and does not require
> authentication, making it **openly accessible to any system or user**."*

And a **"Who Uses This API"** section, which is the part that matters most:

| Audience | Verbatim |
|---|---|
| **Commercial Organisations** | *"Integrating TED data into platforms to provide added-value services for vendors and buyers"* |
| **Researchers** | *"Analysing public procurement trends and patterns"* |
| **Developers** | *"Creating transparency tools or reusing public data"* |
| eNotices2 Users | *"Importing a notice from TED via the web interface"* |

Against §5's checklist:

| Question | Answer |
|---|---|
| Accessing published procurement notices | **yes, explicitly** |
| Analysis | **yes, named twice** |
| Reuse | **yes, named twice** |
| Application integration | **yes** — *"Integrating TED data into platforms"* |
| Commercial reuse | **yes** — commercial organisations named as an audience |
| Repeated queries | **implied** by integration; made explicit by the Open Data Service (§3) |
| Downloading notices | **yes** |
| Automated access | **yes** — *"openly accessible to any system or user"* |

**This is not "an API exists".** §5 forbids reading availability as permission,
and nothing here does. It is the operator stating, in its own documentation, what
the route is for and who it is for.

### Documented limits

From `https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html`:

| Mode | Limits |
|---|---|
| Pagination | up to **15,000** retrievable notices per query; 250 per page; 10,000 fields per page |
| Iteration / scroll | *"Allows the retrieval of all notice documents for a given query, without limitations"*; 250 per page; 10,000 fields per page; *"There is no limit on the number of retrievable notice documents"* |

**No request-rate or concurrency limit is published for either mode.** Absence of
a stated limit is not a stated absence of one, so a collector must throttle
conservatively on its own.

### Field selection

The documented request body carries **`fields: Fields to return for each
notice`**, alongside `query`, `page`, `limit`, `scope`, `paginationMode` and
`iterationNextToken`.

**This matters for §14.** The official query supports field selection, so
minimisation happens **at acquisition** rather than after it. "Collect first,
minimise later" is not available as an excuse on this route.

## 3. The TED Open Data Service — what it says it is for (§6)

`https://data.ted.europa.eu/`, an official EU website, footer: *"This website is
managed by: Publications Office of the European Union."*

Its own words:

> *"**Explore and reuse** EU public procurement data"*

> *"We organise this information as a knowledge graph and **publish it for
> analysis and re-use**. We invite you to explore, understand and use this
> information in **your research and applications**."*

> *"The TED Open Data Service lets you explore the entire collection of public
> procurement data published by the Publications Office of the EU. You can look up
> individual notices and inspect their full RDF graph, or **write SPARQL queries
> to extract custom datasets across many notices**."*

On repeated and automated access, it is explicit:

> *"For SELECT queries, the **Connect your app** button gives you the link, and
> the commands, to **run the same query from your own tools**. You can use this
> URL to run your query and **retrieve live results directly into Excel, Power BI,
> or any application that can get data from the web**."*

The August 2026 changelog offers the same request *"as a cURL, wget or PowerShell
command"*. Results download as JSON, CSV, TSV, Spreadsheet, XML, Turtle, RDF/XML
and N-Triples. The Excel guide says you can *"create a file with a permanent link
to your query and update the data from within Excel whenever you wish"*.

Against §6's checklist: querying **yes**, analysing **yes**, reuse **yes**, use in
applications **yes**, connecting applications **yes**, updating query results
**yes**, automated interaction **yes**.

### The operator's own verb

The Help text says users may **"extract custom datasets across many notices"**.

That is the Directive's verb, used by the operator about its own service, in an
invitation. It is recorded here **because it is striking and because it changes
nothing**: a service description is not a licence, and an operator explaining
what its tool does is not a right holder granting a right in a collection.
Reading it as one would be the same error as reading the CC0 metadata dedication
onto the notice corpus, which Mission 1.15.3 refused.

### The route

| | |
|---|---|
| Documented endpoint | `https://data.ted.europa.eu/` |
| Underlying store | Cellar, Virtuoso — the service front-end issues queries against `https://publications.europa.eu/webapi/rdf/sparql` |
| Authentication | none documented |
| Rate limit | **none published**, and no fair-use statement found |
| Legal notice | footer links to `https://ted.europa.eu/en/legal-notice` — **the same document that governs the bulk route** |

**The Open Data Service adds no new licence.** It inherits the TED legal notice
and therefore Decision 2011/833/EU. That is a finding in both directions: the
H-34 reuse grant reaches it, and the H-36 silence reaches it too.

## 4. Coverage — recent, and partial

From `https://docs.ted.europa.eu/ODS/latest/data_availability.html`:

| Form family | Coverage |
|---|---|
| **eForms** | 1 March 2023 → current day − 1, conforming to ePO v4 |
| **Standard Forms (TEDXML)** | 28 August 2023 → 26 January 2024 only |

And verbatim: *"A limited number of XML notices are available in Cellar. These
were produced during the initial TED Open Data Service Pipeline proof of
concept"* — form types F3, F6, F21, F22, F23, F25, with the remaining form types
and SDK 1.14 *"coming in 2026"*.

**This bounds what the route could support, and it is a coverage fact rather than
a rights fact.** Roughly two and a half years of eForms notices is a usable
transaction window; it is not a decade of history.

## 5. Two response-contract warnings the operator gives itself

Recorded now because a future collector will meet them (§15):

- **Lots duplicate rows.** *"All purchases are organised into lots … it can look
  like data with the same notice number is duplicated in the results table, when
  actually it is showing rows of lots rather than the whole order in one row."*
- **Languages duplicate rows.** *"Notices could be published more than one
  language, so unless you filter for language in the query, the same notice might
  be listed several times in different languages."*

And a monetary caveat the operator states about its own currency-conversion
helper: rates are approximate, applied *"at the latest available rate — not the
rate at the time each notice was published"*, so *"do not rely on the result for
precise or legally meaningful figures"*.

**That is the operator warning against exactly the flattening §15 forbids.**

## 6. What this does NOT establish

Written out because every one of these is a conclusion someone could reach from
the material above, and every one is wrong (§27):

| Not established | Why |
|---|---|
| *"TED has no database rights"* | Nothing retrieved says so. H-36A is untouched |
| *"Local projects do not need permission"* | Permission comes from the source. The local profile changes the risk, not the rule |
| *"Because the API is public, all reuse is allowed"* | §5's own prohibition. The argument rests on documented purpose, not on availability |
| *"Because TED wants reuse, H-36 is irrelevant"* | An operator's enthusiasm for reuse is not a licence over a collection |
| *"Because we are not publishing today, the future SaaS is authorised"* | §8. The commercial multi-tenant profile is unreviewed and stays so |
| *"The Search API is the way around H-36"* | §13. It is not framed as one anywhere in this review |

## 7. Route-by-route (§10)

| Route | Intended-use evidence | Database-right question | State |
|---|---|---|---|
| **TED Search API** | **strong and explicit** — analysis, reuse, integration, commercial audiences, no authentication, field selection | unresolved | **Evidence-supported, not authorised** |
| **TED Open Data Service** (SPARQL) | **strong and explicit** — published for analysis and re-use, connect your app, live results | unresolved | **Evidence-supported, not authorised** |
| **Bulk XML packages** | the reuse docs describe the route, but Mission 1.15.3 established the highest database-right exposure here | unresolved, and this is the exposed case | **BLOCKED**, unchanged |
| **`ted-csv` historical CSV** (DG GROW) | separate dataset, separate publisher, 12 of 48 distributions CC BY 4.0 and 36 `COM_REUSE` over overlapping coverage | unresolved and internally inconsistent | **REVIEW SEPARATELY**, not attempted here |

**"Evidence-supported, not authorised" is the honest state**, and §37 prefers it
to a false claim that H-36 is resolved. What blocks the two query routes is not a
gap in the evidence about them — it is that the registry has no way to say
*"this route, this use profile, yes; that route, that use profile, no"*. See
`route-scoped-source-authorization-gap-v1.md`.

## 8. Bulk XML stays blocked (§12)

Nothing found in this mission changes the bulk route. Mission 1.15.3 established
that one monthly package is ~427 MB and that `COM_REUSE` resolves to a Decision
with no database-right provision. **Public downloadability alone is
insufficient**, and no first-party evidence retrieved here speaks to repeated
substantial extraction.

The bulk route is **not** the default and **not** authorised.

## 9. The future commercial boundary (§8)

If Startup Research OS ever becomes publicly accessible, customer-facing, sold,
subscription-based, multi-tenant, or redistributes TED-derived data at scale,
**the commercial profile must be reviewed again from the top**.

The local profile must never migrate silently. That is the single most likely way
this review could cause harm later, and the gap document proposes the mechanism
that would make the migration impossible rather than merely discouraged.

## 10. Personal data, training, embeddings — unchanged

**Local use justifies collecting no more personal data than commercial use
would** (§18). The minimisation profile is unchanged:

| Keep | Drop |
|---|---|
| notice id; publication date; contract/award date; buyer organisation; supplier organisation; CPV; procurement classification; monetary amount; currency; **monetary amount type**; country/region; award status | natural-person names; personal email; telephone; fax; personal address; the whole contact block; unrelated full text; logos; personal identifiers |

**Model training: still not authorised** (§23). **Embeddings: D-12 open, none**
(§24). **H-34 unchanged and not reopened** (§22).

**Attribution and authenticity survive intact** (§20, §21). A future claim means
*"TED reported…"*, never *"this is the authentic underlying contract"*.

## 11. Retention (§19)

**`NOT_ADDRESSED`.** No retention or caching restriction was found on either
official route, in the API documentation, the Open Data Service, or the legal
notice. Recorded as unaddressed rather than as unlimited, and the platform's own
retention baseline applies where compatible.
