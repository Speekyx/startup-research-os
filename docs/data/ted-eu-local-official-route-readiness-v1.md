# TED-EU Local Official Route Readiness V1

**Authoritative.** Mission 1.15.5 §20–§24, §48. What is authorised under
`local-private-research-v1`, and what still stands between that and a collector.

**State: `APPROVING_BUT_NOT_ELIGIBLE`.** The review is
`APPROVED_WITH_CONDITIONS`; `AcquisitionAuthorizationContext` **cannot be built**;
three human confirmations are outstanding, and one of them is the residual
database-right exposure.

**No collector exists and none may be written from this document alone.**

---

## Source

`ted-eu` · Tenders Electronic Daily · Publications Office of the European Union.

| Profile | Review | Verdict | Eligible |
|---|---|---|---|
| `commercial-multi-tenant-research-v1` | v5 | `REQUIRES_REVIEW` | no |
| **`local-private-research-v1`** | **v1** | **`APPROVED_WITH_CONDITIONS`** | **no** |

## Rights basis

| | |
|---|---|
| **Commission Decision 2011/833/EU** | Article 3(2) defines reuse by **purpose**, not method; Article 4 makes all in-scope documents available commercially, without charge, without application. This grants the six load-bearing activities (H-34, closed by Mission 1.15.2) |
| **TED and SIMAP legal notice** | *"the procurement notices … can be freely reused, for commercial or non-commercial purposes"*. Source of the attribution, authenticity, third-party-rights and industrial-property conditions |
| **`COM_REUSE` dataset metadata** | The data.europa.eu record for `ted-1` declares `dct:license = COM_REUSE` on every distribution, and `COM_REUSE` carries `skos:exactMatch` to the Decision (Mission 1.15.3) |
| **Route intended-use documentation** | The Search API is *"for analysis and reuse"*, *"primarily targeted at data reusers"*, with commercial organisations and researchers named as audiences; the Open Data Service publishes data *"for analysis and re-use"* with a Connect-your-app button (Mission 1.15.4) |

**None of the four is a database-right grant.** H-36 is open, and §"Open
questions" below says so rather than implying otherwise.

## Authorised resource

Contract notices and contract award notices, **eForms**, from **1 March 2023**
onwards — the Open Data Service's documented coverage window.

Dataset families: `ted-search-api-notices`, `ted-open-data-sparql`.
**Excluded by name:** `ted-bulk-xml-daily`, `ted-bulk-xml-monthly`,
`ted-csv-historical`. `require_dataset_family` is true, so an unclassified
resource is denied.

## Access route

| Route | Status |
|---|---|
| **TED Search API** — `https://api.ted.europa.eu/v3/notices/search` | **authorised** |
| **TED Open Data Service (SPARQL)** — `https://data.ted.europa.eu/` | **authorised** |
| Bulk XML packages — `https://ted.europa.eu/packages/` | **BLOCKED**, under every profile |
| `ted-csv` historical subset (DG GROW) | **BLOCKED**, separate dataset, separate licence record |

## Activity status

| | |
|---|---|
| Commercial use | **PERMITTED** — and required to be, because local is not non-commercial |
| Automated access | PERMITTED |
| API use | PERMITTED |
| Storage | PERMITTED (minimised) |
| Retention | PERMITTED |
| Derived analytics | PERMITTED |
| Machine processing | PERMITTED — inference, extraction, classification, structured analysis |
| **Redistribution** | **NOT PERMITTED** under this profile. This is what the profile narrows, and it is why the Article 7(2)(b) re-utilisation limb is not engaged |
| **Model training** | **NOT AUTHORISED** |
| **Embeddings** | **UNASSESSED**, blocked independently by D-12 |

## Attribution

Source credit *"Tenders Electronic Daily (TED), Publications Office of the
European Union"*; licence identifier *Commission Decision 2011/833/EU*; a notice
recording that only electronically signed OJ S notices are authentic and that the
Commission accepts no liability. **The TED and SIMAP logos may not be used.**

The licence identifier is the Decision and **not CC BY 4.0**: CC BY covers the
SIMAP websites' *editorial content*, and citing it over a notice would attribute
the notice to a licence that does not cover it.

## Personal-data minimisation

**Requested through the Search API's `fields` parameter, so minimisation happens
at acquisition** — not after it.

| Keep | Discard |
|---|---|
| notice id · publication date · award date · contract date · buyer organisation · supplier organisation · CPV · procurement classification · monetary amount · **monetary amount type** · currency · country · region · award status | contact point · contact name · contact email · contact telephone · contact fax · postal address · natural-person name · personal identifier |

`monetary_amount_type` is in the keep list deliberately: an amount without its
semantic is the flattening into `price_paid` that nothing downstream can undo.

## Authenticity

A future claim means **"TED reported…"**, never "this is the authentic
underlying contract". Only electronically signed notices published in the
Supplement to the Official Journal are authentic.

## Format, authentication, limits, retention

| | |
|---|---|
| Format | Search API JSON/XML per notice; Open Data Service RDF via SPARQL, downloadable as JSON, CSV, TSV, XML, Turtle, RDF/XML, N-Triples |
| Authentication | **None** for published-notice retrieval on either route. An API key is required only for operations on unpublished notices, which are out of scope |
| Volume limits | Search API pagination: 15,000 retrievable notices per query, 250 per page, 10,000 fields per page. Scroll mode: no notice limit. SPARQL: none published |
| **Request-rate limits** | **UNKNOWN on every route.** No fair-use statement was found for the SPARQL endpoint at all. A collector must throttle conservatively on its own rather than be handed a number nobody published |
| Retention | `NOT_ADDRESSED` by the source; the platform baseline applies |

## Response-contract gaps

Established, and a future collector will meet all of them:

- **Lots duplicate rows.** *"it can look like data with the same notice number is
  duplicated … when actually it is showing rows of lots"*.
- **Languages duplicate rows** unless the query filters language.
- **The currency helper is approximate.** The Open Data Service's own conversion
  snippet warns rates are applied *"at the latest available rate — not the rate
  at the time each notice was published"*, so *"do not rely on the result for
  precise or legally meaningful figures"*.
- Coverage is **eForms from March 2023**; Standard Forms only a documented
  proof-of-concept slice of six form types.

## Monetary semantic gaps

**Nothing may be flattened into `price_paid`.** A future normalizer must
distinguish, from the source's own fields: awarded amount · estimated amount ·
maximum framework amount · lot amount · budget · modification amount ·
range/minimum/maximum · currency. Which of these eForms exposes, and under which
ePO properties, is **not yet established** and is collector-mission work.

## Willingness-to-pay boundary

TED would supply `TRANSACTION_CLASS_PUBLIC_PROCUREMENT_EVIDENCE`: *TED reported
that public buyer X awarded contract Y to supplier Z with reported award value
V*. **It does not measure general SaaS willingness to pay**, and any inference
from a contract award to willingness to pay happens at a later stage, with its
own evidence. Supplier award is not market share, not best competitor, not
product quality.

## Open questions, unchanged

**H-36A — does a sui generis database right subsist?** NOT ESTABLISHED, either
way, under this profile as under the other.

**H-36B — is it granted or waived?** NOT ADDRESSED for broad corpus extraction.

What the local review relies on instead is the operator's own published
intended use for its two query routes, plus the structural fact that the
re-utilisation limb is not engaged by a use that redistributes nothing.
**Neither is a licence.** The review records a judgement about bounded queries
and says the residual exposure is the operator's to accept.

## What stands between this and a collector

`build_authorization('ted-eu', 'local-private-research-v1')` **refuses**:

```text
review conditions not satisfied:
  ted-database-right-residual-exposure-accepted
  ted-official-route-only
  ted-personal-data-minimisation
```

| Condition | Verification | State |
|---|---|---|
| `ted-attribution` | CAPABILITY `source-attribution-display` | **SATISFIED** |
| `ted-official-route-only` | HUMAN_CONFIRMATION | outstanding |
| `ted-personal-data-minimisation` | HUMAN_CONFIRMATION | outstanding |
| `ted-database-right-residual-exposure-accepted` | HUMAN_CONFIRMATION | outstanding |

**No verifier in this repository can satisfy a `HUMAN_CONFIRMATION` condition,
and none ever will.** That is the design, and it is deliberate for the third one:
a residual-risk acceptance that code could satisfy would be a judgement nobody
made. An unconfirmed TED is ineligible rather than quietly usable.

The first two are outstanding for a plain reason as well — **there is no
collector yet**, so there is nothing whose route or field selection a person
could confirm.

## Next mission

**TED Official API Collector V1 — Local Private Research Profile**, if and when
the operator records the three confirmations.

It must: use only the two authorised routes; issue bounded, purpose-scoped
queries; request only the authorised fields through `fields`; discard every
natural-person field; respect unknown rate limits by throttling conservatively;
preserve provenance including the use profile; **never become a TED mirror**; and
remain refused under `commercial-multi-tenant-research-v1`.
