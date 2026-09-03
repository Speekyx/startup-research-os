# Docker commercial scope mapping V1 — the search, and why it found nothing

**Status:** Desk taxonomy research. Authored by Mission 1.35, 2026-09-03.
**Machine-readable record:** [`docker-commercial-scope-mapping-v1.json`](docker-commercial-scope-mapping-v1.json)
**Outcome:** `NO_AUTHORITATIVE_DOCKER_CATEGORY_RELATION_FOUND`
**Relations recorded:** **0 before, 0 after.**

---

## 0. The question, asked in the right direction

Mission 1.34 built the capability to record

```text
PRODUCT subject:docker  --SUBJECT_WITHIN_CATEGORY-->  CATEGORY X
```

and deliberately recorded none. This mission went looking for one.

**§3 fixes the direction of reasoning, and it is the whole methodology.** The
question asked was *what authoritative category, if any, contains the Docker
product?* — never *what category would connect Docker to the commercial evidence
we happen to hold?* CPV was investigated because §7 requires it, after the
product-category question had already been answered, and never as a starting
point. Reversing that order is how a bridge gets built to a destination somebody
picked first.

---

## 1. The answer

**No authoritative taxonomy classifies the Docker container platform into a
category.** Six candidates, six rejections, and they fail in three distinct ways:

| Candidate | What it actually is | Verdict |
|---|---|---|
| Docker's own documentation | a functional description | `REJECTED_DESCRIBES_RATHER_THAN_CLASSIFIES` |
| Open Container Initiative | three specifications | `REJECTED_DEFINES_STANDARDS_NOT_A_TAXONOMY` |
| CNCF Landscape | a curated map | `REJECTED_SUBJECT_ABSENT_AND_SOURCE_IS_A_MAP` |
| Common Procurement Vocabulary | a procurement classification | `CPV_NOT_SUITABLE_FOR_DIRECT_PRODUCT_RELATION` |
| UNSPSC | unreachable (HTTP 403) | `UNRESOLVED_SOURCE_UNREACHABLE` |
| SROS source-native vocabularies | tags and articles with no parents | `REJECTED_NO_SOURCE_NATIVE_PARENT_EXISTS` |

The three failure modes are worth separating, because they are different
problems and only one of them could ever be fixed by looking harder:

- **Things that name Docker but do not classify it.** Docker's own docs and the
  OCI. They describe the product, or use a term for it. A term is not a category:
  it has no identifier, no publisher who decides membership, and no other members.
- **Things that classify products but do not contain Docker.** The CNCF
  Landscape. See §4 — this is the one that failed on a countable fact.
- **Things that classify, but classify something else.** CPV and UNSPSC classify
  what is *bought*. A procurement class contains procurements.

---

## 2. What `subject:docker` is, frozen first (§4)

The Docker container platform, as a subject of published material. Its two
canonical identifiers are the English Wikipedia article `Docker_(software)` and
the Stack Overflow tag `docker`.

**It is not Docker, Inc.** So contracts awarded to the company, its industry
classification, its revenue category and its corporate NAICS or PSC code are all
excluded as evidence about the product — and that exclusion did real work here,
because the one place the CNCF Landscape names Docker unambiguously is
`Docker (member)`, which is the company.

---

## 3. Docker's own documentation describes; it does not classify

`docs.docker.com/get-started/docker-overview/`, retrieved 2026-09-03.

> Docker is an open platform for developing, shipping, and running applications.

The page also uses *"The Docker platform"* and *"Docker's container-based
platform"*. It assigns no categorical label and names no class Docker is a member
of.

**§2 ranks official vendor documentation identifying its own product category
second in priority. Docker's does not identify one.** That is a finding, not an
absence of effort: a functional description is what a vendor writes, and reading
a category out of it would be interpretation presented as a citation.

The Open Container Initiative fails the same way one level up
(`opencontainers.org/about/overview/`, 2026-09-03). It defines three
**specifications** — Runtime, Image, Distribution — records that Docker donated
runC, and uses *container engine* as a term with Docker as an example. It
maintains no register of container engines, so there is nothing to address as a
broader scope.

---

## 4. The CNCF Landscape — the strongest candidate, refused on a fact

This was the candidate worth taking seriously: a Linux Foundation body that
places projects and products into named categories with stable slugs.

**Its data file was read directly** — `landscape.yml` from `cncf/landscape`,
1,138,659 bytes, 2,512 name fields, 15 top-level categories, retrieved
2026-09-03.

**The word *Docker* occurs 53 times, and five items are named for it:**

| Item | Category |
|---|---|
| `Docker Swarm` | Orchestration & Management |
| `Docker Compose` | App Definition and Development |
| `Docker Hub` | (registry / Wasm region) |
| `Docker (Wasm)` | Wasm |
| `Docker (member)` | CNCF Members — **the company** |

**The Docker container platform is not an item in the landscape at all.** Every
one of the remaining 48 occurrences sits inside another product's `description`
or its `summary_integrations` list — Docker as something *other* tools integrate
with.

So the map has no category for the thing `subject:docker` names. Using it would
mean taking the category of a **different artifact** — Swarm is an orchestrator,
Compose is a multi-container definition tool, Hub is a registry — and asserting
it for the platform. That is exactly the trap Mission 1.33 caught one level down,
when PyPI's `docker` package turned out to be the Python SDK rather than the
platform. And the three products sit in **three different categories**, so there
is not even a single wrong answer to be tempted by.

**A second, independent reason, which would have been enough on its own.** The
repository describes itself as *"a map through the previously uncharted terrain
of cloud native technologies"* that *"attempts to categorize most of the projects
and product offerings"*, with an inclusion rule of *"at least 300 GitHub stars"*.
A popularity threshold is not a classification rule: it tells you a project is
well known, not what kind of thing it is. And a source that says it covers *most
of* a space cannot be cited as authoritative for what a particular thing IS.

---

## 5. CPV (§7)

**What CPV classifies: the subject of a procurement.** The Publications Office
records that the Commission drafted it *"to make public procurement more
transparent and efficient"*. Division `48000000` — *Software package and
information systems* — exists and is used across real TED notices, so coarseness
is not the whole objection.

**The decisive point is who assigns a code, and to what.** A contracting
authority assigns a CPV code to **its own contract**. Nobody assigns a CPV code
to a product, and no publisher maintains a product-to-CPV mapping. So a CPV class
contains **procurements**, never products — and a tender that happened to buy
Docker licences would be classified by what that buyer was buying, which is a
fact about the contract and not about the platform.

There is also no container or containerisation class at any depth, and the SROS
TED collector deliberately expands no CPV code into a label, so this repository
does not hold the vocabulary either.

**Verdict: `CPV_NOT_SUITABLE_FOR_DIRECT_PRODUCT_RELATION`**, which §7 names in
advance as a valid finding.

Note what was *not* done: the existing `ted-eu:CPV-division:90` Evidence row was
never treated as evidence of Docker's category (§3, §7). Division 90 is in the
corpus because Mission 1.15.10 ran a bounded test acquisition there. That is a
fact about a test acquisition.

---

## 6. UNSPSC — unresolved, not answered

`unspsc.org` returned **HTTP 403** from this environment on 2026-09-03. No retry
with a varied header, no mirror, no cached copy, no third-party summary.

**Uncertainty is never permission**, and it is not a finding either. Nothing is
asserted about UNSPSC in either direction. It is recorded so a later reviewer
knows it was considered and why it produced nothing.

---

## 7. SROS's own source-native vocabularies (§2 priority 1)

Checked first, because §2 ranks a source-native official taxonomy above
everything else:

- **Stack Overflow tags are flat.** A tag has a description and synonyms; it has
  no parent. `docker` reaches no category.
- **Wikipedia has editorially assigned categories**, and §2 excludes Wikipedia
  interpretation by name.
- **TED publishes CPV**, addressed above.
- **World Bank, FRED, Eurostat and GDELT** publish no product taxonomy at all.

So the highest-priority route has nothing to offer for this subject — and the two
vocabularies that actually *identify* Docker are precisely the two that carry no
parent.

---

## 8. The tests that were never reached (§15, §16)

Recorded so nobody thinks they were skipped. No candidate survived far enough to
be tested for:

- **Overbreadth.** Had a category survived, the question would have been whether
  commercial evidence about it is specific enough to inform *this* Opportunity.
  `software`, `technology`, `IT` and `digital services` would each have been
  rejected as `CATEGORY_TOO_BROAD_FOR_CONTEXT` — a category that broad makes
  almost any commercial dataset look relevant to Docker.
- **Overprecision.** A category amounting to *Docker-like things* would have been
  rejected unless it genuinely exists in an authoritative taxonomy. The broader
  category must exist independently of the Opportunity, and no category may be
  created to bridge Docker to TED.

---

## 9. What follows

**Do not spend further missions on Docker taxonomy.** §30 says so directly, and
the evidence supports it: this is not a case where more searching would help.
Two of the three failure modes are structural — a vendor describing its product
and a standards body defining specifications will not start classifying, and a
procurement vocabulary will not start containing products.

The one candidate that could change is the CNCF Landscape, and only if it began
listing the Docker platform as an item. That is somebody else's editorial
decision, not a research task.

**The recommendation is Reliability / Scoring Eligibility Foundation.** The
Docker packet holds eight rows, all `NON_SCORABLE` for want of a reviewed
reliability, and improving what the system can conclude from the evidence it HAS
does not depend on acquiring or connecting more. D-03 has four open blockers and
this is the one a mission can actually move.

**The alternative, named explicitly because §30 asks for the choice to be
explicit:** begin a second pilot Opportunity in another domain — one whose
subject sits in a published classification, so the multi-scope architecture built
in Mission 1.34 has something real to hold. Docker was chosen as a pilot because
SROS had evidence about it, not because it was well classified; the two turn out
to be different properties.

Between the two, **Reliability first** is the better call: it unblocks scoring
for evidence already held, whereas a second pilot spends acquisition effort
before knowing whether anything can be scored at all.
