# TED-EU Local Official Route Readiness V1

**Authoritative.** Mission 1.15.5 §20–§24, §48, **amended by Mission 1.15.6**.
What is authorised under `local-private-research-v1`, and what still stands
between that and a collector.

**State: `AUTHORIZATION_READY`** (Mission 1.15.6.1). The review is
`APPROVED_WITH_CONDITIONS`, **all four conditions are satisfied**, and
`AcquisitionAuthorizationContext` **builds**. The operator recorded the residual
database-right acceptance on 2026-08-31; the record and its two qualifiers are in
[`ted-eu-operator-risk-acceptance-v1.md`](ted-eu-operator-risk-acceptance-v1.md).

**`AUTHORIZATION_READY` is not a legal clearance and not `resource_ready`.**
H-36A remains `NOT ESTABLISHED` and H-36B remains `NOT ADDRESSED`; and TED
authorises **zero concrete datasets**, so a collector holding the context would
still be refused every resource it asked for.

**Amended by Mission 1.15.6.** Two of the three conditions this document
reported as outstanding described objective properties of the *configuration*
rather than of code, and are now verified against it: `ted-official-route-only`
by the `source-route-binding` capability, `ted-personal-data-minimisation` by
`source-field-minimisation`. Local review **v2** carries the reclassification and
changed no policy conclusion. See
[`ted-eu-authorization-bootstrap-v1.md`](ted-eu-authorization-bootstrap-v1.md).

**No collector exists and none may be written from this document alone.**

---

## Source

`ted-eu` · Tenders Electronic Daily · Publications Office of the European Union.

| Profile | Review | Verdict | Eligible |
|---|---|---|---|
| `commercial-multi-tenant-research-v1` | v5 | `REQUIRES_REVIEW` | no |
| **`local-private-research-v1`** | **v2** | **`APPROVED_WITH_CONDITIONS`** | **no** |

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

| Route | Access profile | Status |
|---|---|---|
| **TED Search API** — `https://api.ted.europa.eu/v3/notices/search` | `ted-search-api` | **authorised**, and the **preferred first implementation route** |
| **TED Open Data Service (SPARQL)** — `https://data.ted.europa.eu/` | `ted-open-data-sparql` | **authorised** |
| Bulk XML packages — `https://ted.europa.eu/packages/` | `ted-bulk-xml` | **BLOCKED BY NAME**, under every profile |
| `ted-csv` historical subset (DG GROW) | *(no route)* | **BLOCKED** at the resource gate, separate dataset, separate licence record |

**Enforced, not promised** (Mission 1.15.6). The authorised labels are a
`route_authorization` in `source-compliance-v1.json`, and
`build_authorization` puts **only those routes** into `context.access` — so
`ted-bulk-xml` has no endpoint a collector could reach, no host to allowlist and
nothing for the transport to be pointed at. `ted-open-data-sparql` was
registered as an access profile in the same mission, because the review
authorised a route the registry did not record.

The Search API is **preferred** for the first collector: it publishes explicit
intended-use documentation, supports field selection through `fields` so
minimisation happens at acquisition, and has a simpler response contract than
SPARQL. That is an implementation choice among authorised routes and widens
nothing.

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

**Enforced, not promised** (Mission 1.15.6). `context.authorize_fields(...)`
refuses an excluded field by name, a field no review authorised, and a request
that states no field selection at all — before a request is composed. There is
deliberately no method that strips fields out of a collected record: a request
that took the contact block and discarded it afterwards would have retrieved the
contact block.

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

`build_authorization('ted-eu', 'local-private-research-v1')` **succeeds**, given
the complete verification set — the three live capability results plus the
recorded operator decision:

```text
  use profile   local-private-research-v1
  review        v2  APPROVED_WITH_CONDITIONS
  routes        ted-open-data-sparql, ted-search-api
  ted-bulk-xml  ABSENT
  preferred     ted-search-api
```

What still stands between this and a **collector** is no longer a permission. It
is a concrete resource: TED authorises zero datasets, so `resource_ready` is
**no**.

| Condition | Verification | State | Established by |
|---|---|---|---|
| `ted-attribution` | CAPABILITY `source-attribution-display` | **SATISFIED** | the live verifiers |
| `ted-official-route-only` | CAPABILITY `source-route-binding` | **SATISFIED** | the live verifiers |
| `ted-personal-data-minimisation` | CAPABILITY `source-field-minimisation` | **SATISFIED** | the live verifiers |
| `ted-database-right-residual-exposure-accepted` | HUMAN_CONFIRMATION | **SATISFIED** | a recorded operator decision, 2026-08-31 |

**No verifier in this repository can satisfy a `HUMAN_CONFIRMATION` condition,
and none ever will.** That is the design, and it is deliberate for this one: a
residual-risk acceptance that code could satisfy would be a judgement nobody
made. An unconfirmed TED is ineligible rather than quietly usable.

**What Mission 1.15.6 changed, and what it did not.** This document previously
recorded the first two as outstanding for a plain reason — *there is no collector
yet, so there is nothing whose route or field selection a person could confirm*.
That was a bootstrap, and it broke in the wrong direction: it invited writing the
collector first and confirming it afterwards. Both conditions turned out to
describe the **configuration handed to authorization** rather than code, and both
are now checked against it, with no network call and no collector. The third was
left exactly where it was, because it is a judgement rather than a property.

**The exact operator statement** that a later, explicit action must record is in
[`ted-eu-authorization-bootstrap-v1.md`](ted-eu-authorization-bootstrap-v1.md)
§6.2. Nothing has been recorded, and the existence of that text is not an
acceptance.

**The acceptance was recorded on 2026-08-31**, at the second attempt. A first,
shorter statement was **refused** because three of §6.2's seven items were
absent, including the clause that gives the acceptance a boundary; that refusal
and its reasoning are preserved in
[`ted-eu-operator-acceptance-pending-v1.md`](ted-eu-operator-acceptance-pending-v1.md).
The operator then supplied the complete acknowledgement, and one
`HUMAN_CONFIRMATION` row was written against `ted-eu` ·
`local-private-research-v1` · review v2 · actor `local-operator`. See
[`ted-eu-operator-risk-acceptance-v1.md`](ted-eu-operator-risk-acceptance-v1.md).

**The `verify --apply` warning is lifted** (Mission 1.15.6.2). A machine pass
now leaves a human condition untouched — no row, no cleared boolean — and says so
in its output. Running the verifiers no longer revokes a decision nobody
withdrew, and `sros-source authorization ted-eu` builds the context through the
normal path without any caller merging verification sources by hand. See
[`effective-condition-verification-v1.md`](effective-condition-verification-v1.md).

## Next mission

**TED Official Search API Collector V1 — Local Private Research Profile**, if and
when the operator records the one remaining confirmation.

It must: obtain its route from `context.access` and bind to `ted-search-api`;
request only the fields `context.authorize_fields` permits; issue bounded,
purpose-scoped queries; discard every natural-person field; respect unknown rate
limits by throttling conservatively rather than against an invented number;
preserve provenance including the use profile; distinguish every monetary
semantic rather than flattening into `price_paid`; **never become a TED mirror**;
and remain refused under `commercial-multi-tenant-research-v1`.

**It must also be built so that it cannot execute without an authorized
configuration**, the way `test_collector_conformance.py` already asserts for
resource access. The route and field gates establish that the configuration is
correct; only the collector's own structure can establish that it went through
them.
