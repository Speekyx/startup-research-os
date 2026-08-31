# Mission 1.15.3 — TED-EU Database-Right Clarification & Bulk-Package Licence Audit

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.3` · **Scope:** one open
question, exhausted against first-party material and then externalised.

**Outcome C — H-36 OPEN / `EXTERNAL_CLARIFICATION_REQUIRED`.**

The licence attached to the assembled TED dataset **exists**, is
machine-readable, and **is Commission Decision 2011/833/EU** — the instrument
already read in full and already known to be silent on database rights. Both
access routes are governed by that same silence.

**TED stays `REQUIRES_REVIEW` at review v4.** The clarification request is
written and **unsent**.

---

## 0. What changed

The blocker did not move, but it changed from *"a legal question the documents do
not answer"* into *"a legal question with a named addressee, a drafted message
and five specific asks"*.

Mission 1.15.2 established that **one document** is silent. This mission
established that **the whole chain** is — catalogue records, authority tables,
API specification, HTTP headers and every enclosing legal notice — and found the
one place a licence that *would* reach the right does appear, on files that are
not the ones we need and applied inconsistently to those.

---

# The §39 questions

## What exactly is H-36 now?

**Two questions with different addressees**, tracked separately from review v4:

| | State |
|---|---|
| **H-36A** — does a sui generis database right subsist in the TED notice corpus, and who holds it? | **NOT ESTABLISHED, either way** |
| **H-36B** — does the applicable right holder grant or waive extraction and re-utilisation? | **NOT ADDRESSED for both routes** |

## Was any new TED-specific dataset licence discovered?

**Yes, and it is the mission's main finding.** The Publications Office publishes
TED in its own open-data catalogue, and the DCAT-AP record declares
`dct:license = COM_REUSE` on **every** distribution of `ted-1`.

```text
https://data.europa.eu/api/hub/repo/datasets/ted-1.rdf
```

| Distribution | Type | `dct:license` |
|---|---|---|
| Procurement notices by place of performance | WEB_SERVICE | `COM_REUSE` |
| Procurement notices by business sector | WEB_SERVICE | `COM_REUSE` |
| Procurement notices by type of business opportunity | WEB_SERVICE | `COM_REUSE` |
| **Last daily editions of procurement notices in bulk download** | **DOWNLOADABLE_FILE** | **`COM_REUSE`** |

And `COM_REUSE` carries **`skos:exactMatch` → `http://data.europa.eu/eli/dec/2011/833/oj`**.

**So the licence on the bulk route is the Decision**, by the publisher's own
machine-readable assertion. Finding it strengthens the reasoning and does not
change the answer.

## Does any licence explicitly cover the assembled TED database?

**No.** `COM_REUSE` covers the distributions; what it *contains* is a documents
reuse policy. No licence anywhere names the collection as its subject.

The `ted-1` dataset node itself carries **no `dct:license`**, **no
`dct:rights`** and **no `dct:creator`**.

## Does CC0 apply to the notice corpus or only SIMAP metadata?

**Only the metadata**, verbatim: *"The SIMAP's system metadata is dedicated to
the public domain in accordance with the Creative Commons Universal Public Domain
Dedication deed (CC0 1.0)."*

The boundary Mission 1.15.2 drew holds. One honest caveat, which became a
question rather than a finding: **the notice nowhere defines "system metadata"**.
If it covered the structured fields of published notices, CC0 would waive sui
generis rights over exactly the fields the engine wants — so that reading is the
one to distrust, and it is question 5 in the clarification request.

## Does CC BY apply to the dataset/database or only other material?

**In the TED legal notice: only website editorial content**, verbatim: *"The
copyright over the editorial content of the SIMAP websites (TED, TED eNotices2,
TED Developer Docs and TED Developer Portal) is licensed under … CC BY 4.0."*

**In the data.europa.eu catalogue: on 12 distributions of a different dataset.**
See below — this is the mission's sharpest finding and it is not a grant we can
use.

## Who is identified as the database producer/right holder, if anyone?

**Nobody.**

`ted-1` names `dct:publisher = corporate-body/PUBL` (Publications Office of the
European Union) and carries **no `dct:creator`**. TED's own footer says *"This
website is managed by: Publications Office of the European Union."*

**A publisher is not a maker.** Notices are filed by contracting authorities
across the Union through eSenders and eNotices2. Nothing retrieved asserts who
assembled the collection in the Article 7(1) sense, or that anyone made a
substantial investment in obtaining, verifying or presenting its contents.

## Is a sui generis database right established to subsist?

**No.**

## Is it established not to subsist?

**No.** Both directions are unestablished, and saying so is the finding. §10
forbids concluding it from architecture, and nothing here does.

## Is extraction addressed?

**No.** Zero occurrences across every TED and Publications Office document
retrieved.

## Is re-utilisation addressed?

**No.** Zero occurrences.

## Is repeated/systematic extraction addressed?

**No** — not by any TED or Publications Office material. It *is* addressed by
Directive 96/9/EC Article 7(5), which is why it appears in the legal packet: the
Article reaches repeated and systematic extraction of *insubstantial* parts, so
it bears on the API route as well as the bulk one.

## Does bulk XML have an explicit database-right grant?

**No.** It has an explicit **licence** — `COM_REUSE` — and that licence contains
no database-right provision.

## Does the search API have an explicit database-right grant?

**No.** Its OpenAPI document has a section headed **Terms of Usage** whose entire
content is one link:

```html
<li><a href="https://ted.europa.eu/en/legal-notice">Legal notice</a></li>
```

## Are bulk XML and API materially different under H-36?

**Less than Mission 1.15.2 recorded, and this is a correction rather than a
refinement.**

| | Bulk XML | Search API |
|---|---|---|
| Governing terms | `COM_REUSE` → the Decision | Terms of Usage → the TED legal notice |
| Database-right provision | none | none |
| Documented volume ceiling | none | pagination 15k per query; **scroll: no limit on retrievable notices** |
| One request transfers | 16.7 MB daily / **427 MB monthly** | 250 notices per page, unbounded pages in scroll mode |

Mission 1.15.2 reasoned the API was *"less obviously a substantial part … and
correspondingly less exposed"*. Two facts weaken that: the API's own
specification documents a **scroll mode with no limit on the number of
retrievable notices**, and Article 7(5) reaches repeated extraction of
insubstantial parts regardless of per-request size.

**Both remain analysed separately, both remain unresolved, and no route was
preferred.** The 1.15.2 document carries a banner recording the correction rather
than being silently patched.

## What is H-36A's state?

**NOT ESTABLISHED.** Article 7(1) makes subsistence turn on a **maker** and a
**substantial investment**; no first-party document names either, the catalogue
names a publisher and no creator, and Article 11 then makes it depend on facts
about that maker. **A legal question about facts nobody has published, not a
retrieval gap.**

## What is H-36B's state?

**NOT ADDRESSED.** Article 7(3) confirms the right *"may be transferred, assigned
or granted under contractual licence"*. The licence that governs both routes does
not do so.

## Is H-36 CLOSED or OPEN?

**OPEN — `EXTERNAL_CLARIFICATION_REQUIRED`.**

§15 lists three ways it could have closed permitted. None was met: the right is
not established not to apply; no right holder grants or waives it; and the
governing instrument does not cover it for either route. §15's forbidden reasons
— public downloadability, no authentication, the API existing, probable intent —
were all available and all refused.

## Did TED's verdict change?

**No.** `REQUIRES_REVIEW`.

## What is the current review version?

**4.** v1, v2 and v3 are unmodified and asserted so.

## Is TED collector-eligible?

**No.**

## Can AcquisitionAuthorizationContext be built?

**No.** A context requires an approving source.

## Did H-34 remain CLOSED?

**Yes**, and untouched (§24). All six load-bearing activities remain `PERMITTED`.
A test asserts that no open question mentions H-34 — the reuse grant is settled
and this mission had no business reopening it.

## Were existing nine conditions preserved?

**Yes, verbatim.** A tenth was added:

> The licence that governs a TED resource must be resolved from **that
> resource's own** first-party record, and never carried across from another.

It names both datasets and both licences explicitly, so a future collector cannot
read the CSV subset's CC BY files onto the XML corpus.

## Was personal-data minimisation preserved?

**Yes**, unchanged. Keep: notice id, award value, currency, buyer organisation,
supplier organisation, CPV, dates. Drop: the entire natural-person contact block.
Asserted by test, and restated in the clarification request so the operator's own
message commits to it.

## Was a clarification request produced?

**Yes** — `docs/data/ted-eu-database-right-clarification-request-v1.md`, with all
eleven §18 items present and mapped in a checklist inside the document.

## What exact question should be sent to the Publications Office?

Two, verbatim from the request:

> 1. **Does the European Commission or the Publications Office assert a sui
>    generis database right, or any other database-level right, over the
>    collection of TED procurement notices?**
>
> 2. **If so, does the reuse policy implemented by Commission Decision
>    2011/833/EU — as reflected in the `COM_REUSE` licence declared on the TED
>    dataset — authorise the repeated extraction and re-utilisation of
>    substantial parts of that collection for commercial analytical services,
>    including automated machine processing?**

Plus three the documents made possible: whether the answer differs between bulk
and API (§20), whether the CC BY 4.0 / `COM_REUSE` split in the catalogue is
intentional, and what *"the SIMAP's system metadata"* covers.

The request states our use **without narrowing it** — commercial reuse, storage
and automated processing are all named — because a permission obtained by
describing a smaller product is a permission for a product we are not building.

## What contact route was identified?

| | |
|---|---|
| **Primary** | `op-copyright@publications.europa.eu` — from the TED legal notice: *"For all other copyright issues regarding SIMAP, please contact…"* |
| **Secondary** | `GROW-D2@ec.europa.eu` — from the `ted-csv` dataset description, for the CSV-subset question only |
| **Fallback** | The TED helpdesk contact form |

Both addresses are published by the operator in its own first-party material.

## Was anything claimed as sent?

**No.** The request is marked `PREPARED — AWAITING OPERATOR SEND`, says *"Nothing
has been transmitted"*, and there is no `sent_at` field anywhere in the
repository. A test asserts all three.

## Was a legal-review packet produced?

**Yes** — `docs/data/ted-eu-h36-legal-review-packet-v1.md`. Established facts
only, the operative provisions of both instruments quoted from their own
retrieved text, five questions, and **no legal conclusion**. It records the
unfavourable outcome in advance so it reads as a question rather than as
advocacy.

## Was any collector implemented?

**No.** Asserted twice — against `IMPLEMENTED_COLLECTORS` and
`IMPLEMENTED_NORMALIZERS`, and against the file tree, because "no collector"
checked only against a registry is a check a new module could forget to join.

## Was any TED research data collected?

**No.** HEAD requests read package headers; **no package body was downloaded**.
Whether a licence or README travels *inside* the archives is recorded as
unestablished — the §4 outcome, reached rather than worked around.

## Were RawRecords/NormalizedRecords/Signals created?

**No.** Zero rows with `source_id = 'ted-eu'`, asserted live.

## Were Claims/Evidence generated?

**No.** Policy and catalogue metadata is not research evidence.

## Were reliability assessments created?

**No.** 0, asserted. Rights review and reliability stay independent.

## Were Opportunities generated?

**No.** 0.

## Was scoring performed?

**No.**

## Did the existing 12 / 12 / 7 / 7 / 7 remain unchanged?

**Yes** — per the pytest post-suite digest watcher across 24 tenant and 16 global
tables. Verdict distribution unchanged: `APPROVED_WITH_CONDITIONS` 5,
`REQUIRES_REVIEW` 13, `RESTRICTED` 8, `PROHIBITED` 3 across 29 sources.

## If H-36 closes favourably, is TED Collector V1 now the next mission?

**Not yet, and the readiness document was deliberately not written** (§35's
Outcome A did not obtain).

If a first-party answer closes H-36 favourably, TED would become
`APPROVED_WITH_CONDITIONS` subject to all ten conditions being representable in
compliance configuration, and `ted-eu-collector-readiness-v1.md` would come
before any collector.

## If H-36 remains open, what exact external action is required?

**Send the prepared request to `op-copyright@publications.europa.eu`.** One
email. The message is written, the questions are specific, and the address is the
operator's own.

If the answer does not settle it, hand
`ted-eu-h36-legal-review-packet-v1.md` to a lawyer.

## If TED becomes restricted, is USAspending now the P0 WTP candidate?

**Yes** — and it is worth starting on it now rather than after a reply.

`usaspending` (H-35, licence unreviewed) is the only other registered
transaction-class candidate. Reviewing it does not compete with waiting for a
reply, so the priority document recommends it **in parallel, not instead**. TED
stays P0 because it is the only route to European transaction evidence, and §37
is explicit that human review being needed is not a reason to abandon a source.

**USAspending was not re-reviewed in this mission.** Scope stayed narrow.

---

## 1. Three things worth recording

**The licence was in the catalogue, not in the legal notice.** Three missions
read TED's legal notice, the Publications Office's copyright notice and the
Decision, and none of them looked at the DCAT record — where the publisher states
the licence in a field, per distribution, machine-readably. The general lesson:
**for a published dataset, the rights statement a human reads and the rights
statement a machine reads are different documents, and the second one is the one
attached to the file you will actually download.**

**The most useful find was the one that does not help.** The CC BY 4.0 files are
the only place in this whole investigation where a first-party licence reaches
the sui generis right. Two facts stopped them being an answer — a different
dataset under a different publisher, and an assignment that puts overlapping
coverage under both licences. Recording the favourable fact in full and then
declining to use it is what makes the refusal honest rather than convenient, and
a test asserts both halves are in the same evidence entry.

**A structural guard matched its own source, for the third time.** The
no-network check was written as a substring scan and failed on its own list of
forbidden substrings — after the normalization guard and after Mission 1.13's
vocabulary guard refused the example §3 used to explain itself. Rewritten over
the AST, which cannot match its own literals and is stricter besides. The rule is
now stated plainly in `testing-strategy.md` §38: **a guard expressed over a
file's text eventually matches the text explaining the guard.**

## 2. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | 515 tests, 8 packages, pass |
| Pytest suites | 7 packages, pass; database unchanged across 24 tenant and 16 global tables |
| `validate_source_registry` | pass — 29 sources, 45 evidence records, 0 warnings |
| All other validators | pass |
| Generated catalog documents `--check` | current |
| New tests | 45, plus 7 existing repinned |
| `ruff` / `mypy` | pass |

## 3. Where TED stands

**One email away from an answer, or from a legal question.**

Every document has been read. The catalogue has been read, the authority tables
have been read, the API specification has been read, and the package headers have
been read. There is nothing left to retrieve, which is exactly why the next step
is a message rather than a fetch.

The most likely outcomes are both useful. A first-party answer closes H-36 in
either direction and the portfolio either gains its first transaction-class
source or stops spending effort on one it cannot have. Silence sends it to legal
review with a packet that costs a reviewer hours rather than days.

**What did not happen is the point.** A dataset-level licence was found on the
exact route a collector would use, a sibling dataset was found under a licence
that expressly grants the right in question, and the source is still blocked —
because neither of those is a grant over the TED corpus, and saying so was the
only honest reading available.
