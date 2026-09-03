# Mission 1.35 — Docker Commercial Scope Mapping V1

**Outcome:** `NO_AUTHORITATIVE_DOCKER_CATEGORY_RELATION_FOUND` (§28 C)

**Branch:** `sprint-1/mission-1.35`
**Desk research:** [`docker-commercial-scope-mapping-v1.md`](../data/docker-commercial-scope-mapping-v1.md)
**Machine-readable record:** [`docker-commercial-scope-mapping-v1.json`](../data/docker-commercial-scope-mapping-v1.json)

---

## 0. The finding

**No authoritative taxonomy classifies the Docker container platform into a
category.** Six candidates were examined and all six were rejected, in three
distinct ways:

- **Names Docker, does not classify it** — Docker's own documentation, the OCI.
- **Classifies products, does not contain Docker** — the CNCF Landscape.
- **Classifies, but classifies something else** — CPV and UNSPSC classify what is
  *bought*.

The relation registry held 0 relations before and holds **0 after**. All thirteen
research counters are unchanged.

---

## 1. The thirty-three answers

### 1. Which authoritative sources were inspected?

Six, each with its document and retrieval date recorded in the JSON artifact:

| Source | Document | Result |
|---|---|---|
| Docker, Inc. | `docs.docker.com/get-started/docker-overview/` | describes, does not classify |
| Open Container Initiative | `opencontainers.org/about/overview/` | defines specifications |
| CNCF | `github.com/cncf/landscape` + its `landscape.yml` | subject absent from the map |
| Publications Office (CPV) | `op.europa.eu` EU Vocabularies CPV dataset | classifies procurements |
| GS1 US (UNSPSC) | `unspsc.org` | **HTTP 403**, unresolved |
| SROS's own sources | `source-catalog-v1.json`, canonical subject registry | no parents exist |

EUR-Lex was attempted for the CPV regulation and returned an empty body, as it
did in Missions 1.15.2 and 1.15.3. No mirror was used.

### 2. What exactly does `subject:docker` represent?

The Docker container platform, as a subject of published material, identified by
the English Wikipedia article `Docker_(software)` and the Stack Overflow tag
`docker`. **Not Docker, Inc.** — and that exclusion did real work, because the
one unambiguous Docker entry in the CNCF Landscape is `Docker (member)`, the
company.

### 3. Which candidate categories were considered?

Every category any inspected source offered: the CNCF Landscape's top-level
categories (Runtime, Orchestration & Management, App Definition and Development,
Platform, Serverless, Wasm and the rest), CPV division `48000000` *Software
package and information systems*, and the term *container engine* as the OCI uses
it.

### 4. Which were rejected?

All of them.

### 5. Why?

Each for its own reason, and the reasons are not interchangeable:

- **Docker's documentation** — *"Docker is an open platform for developing,
  shipping, and running applications."* A functional description. It assigns no
  categorical label and names no class Docker belongs to. §2 ranks vendor
  documentation identifying its own category second; Docker's does not identify
  one.
- **OCI** — defines three specifications (Runtime, Image, Distribution), records
  that Docker donated runC, and uses *container engine* as a term with Docker as
  an example. **A term is not a category**: it has no identifier, no publisher
  deciding membership and no member list, so there is nothing to put in a
  relation's broader endpoint.
- **CNCF Landscape** — see question 9's detail. Rejected on a countable fact.
- **CPV** — see questions 6 to 8.
- **UNSPSC** — unreachable.
- **SROS source-native vocabularies** — Stack Overflow tags are flat (a tag has
  synonyms and a description, no parent); Wikipedia categories are excluded by §2
  by name; TED publishes CPV; the rest publish no product taxonomy. **The two
  vocabularies that actually identify Docker are precisely the two that carry no
  parent.**

### 6. Was CPV considered?

Yes, as §7 requires — and **after** the product-category question had been
answered, never as a starting point. §3 fixes that direction and it is the whole
methodology: the question asked was *what authoritative category contains the
Docker product?*, not *what category would connect Docker to the commercial
evidence we happen to hold?*

The existing `ted-eu:CPV-division:90` Evidence row was never treated as evidence
of Docker's category. Division 90 is in the corpus because Mission 1.15.10 ran a
bounded test acquisition there, which is a fact about a test acquisition.

### 7. What does CPV classify?

**The subject of a procurement.** The Publications Office records that the
Commission drafted the CPV *"to make public procurement more transparent and
efficient"*. Division `48000000` *Software package and information systems*
exists and appears across real TED notices, so coarseness alone is not the
objection.

### 8. Is CPV directly suitable for a Docker PRODUCT relation?

**No. `CPV_NOT_SUITABLE_FOR_DIRECT_PRODUCT_RELATION`.**

The decisive point is **who assigns a code, and to what**: a contracting
authority assigns a CPV code to **its own contract**. Nobody assigns one to a
product, and no publisher maintains a product-to-CPV mapping. A CPV class
therefore contains procurements and never products — a tender that bought Docker
licences would be classified by what that buyer was buying, which is a fact about
the contract.

There is also no container or containerisation class at any depth, and the SROS
TED collector deliberately expands no CPV code into a label, so this repository
does not hold the vocabulary either.

### 9. Was one CATEGORY selected?

**No.** The nearest miss deserves its detail, because it was rejected on a fact
rather than on a judgement about authority.

The CNCF `landscape.yml` was read directly: **1,138,659 bytes, 2,512 name fields,
15 top-level categories**. The word *Docker* occurs **53 times**, and **five items
are named for it**:

| Item | Category |
|---|---|
| `Docker Swarm` | Orchestration & Management |
| `Docker Compose` | App Definition and Development |
| `Docker Hub` | registry / Wasm region |
| `Docker (Wasm)` | Wasm |
| `Docker (member)` | CNCF Members — the **company** |

**The Docker container platform is not an item in the landscape at all.** The
other 48 occurrences sit inside another product's `description` or
`summary_integrations` — Docker as something other tools integrate with.

So there is no category of the map's to borrow. Using one would mean taking the
category of a **different artifact** — Swarm orchestrates, Compose defines
multi-container applications, Hub is a registry — and asserting it for the
platform. That is the trap Mission 1.33 caught one level down, when PyPI's
`docker` package turned out to be the Python SDK. And the three products sit in
**three different categories**, so there is not even a single wrong answer to be
tempted by.

A second and independently sufficient reason: the repository calls itself *"a map
through the previously uncharted terrain"* that *"attempts to categorize most of
the projects and product offerings"*, with an inclusion rule of *"at least 300
GitHub stars"*. **A popularity threshold is not a classification rule.**

### 10. Exact category id?

None. `relation_sought.broader_scope_id` is `null` in the artifact.

### 11. Exact category label?

None.

### 12. Relation origin?

Not applicable — no relation. Had one been recorded, §10 would have required
`HUMAN_REVIEWED` rather than `SOURCE_NATIVE` for anything requiring a person to
interpret documentation, because hidden interpretation presented as source-native
is the failure that rule exists to prevent.

### 13. Relation basis?

Not applicable. What *is* recorded is the basis for each **refusal**, with the
document, the section or identifier, and the retrieval date — so another reviewer
can reach the same conclusion from the same documents (§23) rather than taking
this one on trust.

### 14. Relation status?

Not applicable. §11 forbids an *almost active* relation created so downstream
context can flow, and none was created in any status.

### 15. Was a ScopeRelation persisted?

**No.**

### 16. How many active scope relations before/after?

**0 → 0.**

The registry now records **why** it is empty: a third `explicitly_not_recorded`
entry attributed to `mission-1.35`, summarising the search. *Empty because nobody
looked* and *empty because somebody looked* are different facts, and a test
asserts the distinction is visible.

### 17. Does the relation mean Docker equals the category?

No relation exists. The boundaries were written down anyway, in
`relation_sought.would_never_have_meant`, because the next mission that attempts
one starts from them: not that Docker equals the category, not that observations
about the category apply to Docker, not that Docker represents the category, not
that the category's economic value, buyers or demand are Docker's.

### 18. Did any broader Evidence become direct?

**No.** Nothing was attached, so nothing was promoted.

### 19. Did Docker gain `MARKET_ACTIVITY`?

**No.**

### 20. Did Docker gain `ECONOMIC_VALUE`?

**No.**

### 21. Did Docker gain `BUYER_OR_BUDGET_EXISTENCE`?

**No.**

### 22. Did Docker gain WTP?

**No** (§18). Direct dimensions are still exactly `AUDIENCE_OR_USAGE` and
`PROBLEM_OR_NEED`, asserted against the Mission 1.34 demonstration artifact.

### 23. Was TED Evidence attached?

**No** (§12). Contextual evidence is still 0 and scope relations used is still 0.
Even had a relation been found, §12 forbids attachment in this mission.

### 24. Was the Opportunity revised?

**No.** One Opportunity, one revision, still revision 1.

### 25. Were Evidence links changed?

**No.** Still 7.

### 26. Were canonical research records created?

**No.** External documents were read for the taxonomy question only and **none
was ingested** into the research pipeline (§20). The CNCF data file was read in
memory to count entries; no RawRecord, NormalizedRecord, Signal, Claim or
Evidence was created from it or from anything else.

### 27. Were model calls made?

**No.** 0.00 USD. No semantic classification, no embeddings, no fuzzy matching,
no vector similarity. Every finding is a quotation or a count from a first-party
document.

### 28. Were network research documents consulted?

**Yes**, and only for this bounded taxonomy question, as §2 permits. Six
first-party or publisher-operated sources, listed in question 1, each with its
retrieval date. No blog, SEO page, Reddit thread, vendor comparison, analyst
piece or search-engine snippet was used as a basis, and no model recall was
substituted for a document.

### 29. Did scoring/ranking occur?

**No.** `scoring.scores` still does not exist; D-03 untouched.

### 30. Is reliability unchanged?

**Yes.** One `ReliabilityAssessment`, unchanged. Every Docker row is still
`NON_SCORABLE` with `MISSING_RELIABILITY`.

### 31. Is independence unchanged?

**Yes.** `UNKNOWN` everywhere, 0 `EvidenceIndependenceGroups`.

### 32. Is Problem-Family still PARKED?

**Yes.** `PARK_PROBLEM_FAMILY_CLASSIFIER` stands; production inference remains
`NOT_AUTHORISED`.

### 33. Recommended next mission?

**Reliability / Scoring Eligibility Foundation**, and §30 asks for the choice to
be explicit, so here it is.

§30 says that on this outcome SROS should stop spending missions on Docker
taxonomy and choose between Reliability and a second pilot Opportunity in another
domain.

**Do not keep searching.** Two of the three failure modes are structural: a
vendor describing its product and a standards body defining specifications will
not start classifying, and a procurement vocabulary will not start containing
products. The only candidate that could change is the CNCF Landscape, and only if
it began listing the Docker platform as an item — somebody else's editorial
decision, not a research task.

**Reliability over a second pilot**, because it unblocks scoring for evidence
already held, whereas a second pilot spends acquisition effort before knowing
whether anything can be scored at all. The Docker packet's eight rows are all
`NON_SCORABLE` for want of a reviewed reliability, and D-03 has four open
blockers of which this is the one a mission can actually move.

**The second pilot remains the right call later**, and this mission sharpened why:
Docker was chosen as a pilot because SROS had evidence about it, not because it
was well classified. Those turn out to be different properties, and a future pilot
subject should be chosen partly for sitting in a published classification — so
that the multi-scope architecture Mission 1.34 built has something real to hold.

---

## 2. Canonical counters (§27)

Verified against the live database.

| Counter | Expected | Actual |
|---|---:|---:|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / Evidence | 28 each | **28 each** |
| ClaimRevisions | 29 | **29** |
| EvidenceIndependenceGroups | 0 | **0** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / revisions / links | 1 / 1 / 7 | **1 / 1 / 7** |
| Embeddings / Scores | 0 / 0 | **0 / 0** |
| Registered sources | 29 | **29** |
| Latest migration | 0031 | **0031** |
| **Scope relations** | 0 | **0** |

---

## 3. Tests

24 added in
[`test_docker_scope_mapping.py`](../../packages/opportunity-engine/python/tests/test_docker_scope_mapping.py);
353 passing in the package.

Because no relation was added, §26's second branch applies: the tests hold the
documented refusal and the zero-relation state. Every candidate names a document
and a retrieval date; the CNCF rejection is pinned to its countable facts; an
unreachable source stays `UNRESOLVED` with `None` rather than `False`; product
identity stays separate from company identity; Docker's direct dimensions are
still exactly two; and TED is still unattached.

One test of mine was too crude and was narrowed rather than deleted — the third
instance of `testing-strategy.md` §23 across three missions. A scan forbidding the
word *embedding* failed on the artifact's own sentence forbidding embeddings, so
it now reads the candidate rows, where a mechanism would actually be proposed.

---

## 4. CI-equivalent verification

| Gate | Result |
|---|---|
| `generate.py --check` | ok |
| `run_python_tests.py` | all suites passed |
| `validate_schema.py` / `migrate.py --plan` | ok, ledger at 0031 |
| `validate_source_registry.py` | 29 sources, 0 warnings |
| `validate_compliance_capabilities.py` | ok |
| `validate_normalization.py` / `validate_signals.py` / `validate_claims.py` | ok |
| `validate_evidence_aggregation.py` | scoring still blocked |
| `ruff check` / `ruff format --check` | clean |
| `mypy` (13 packages) | no issues |
| generated-doc `--check` steps (4) | all match |
| `run_pytest_suites.py` | passed across 9 packages; database unchanged |
