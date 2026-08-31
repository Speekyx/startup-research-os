# Mission 1.15.6.1 — TED-EU Explicit Operator Residual-Risk Acceptance

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.6.1` · **ADR:** none

**This mission ran twice.** The first run returned **Outcome B** and is recorded
below, unchanged. The second run returned **Outcome A**: the operator supplied
the complete acknowledgement and one verification row was written. **Skip to
"Completion" for the final state**; everything before it describes the first
attempt and is preserved because the refusal is why the recorded acknowledgement
is the complete one.

---

## First run — Outcome B

**Outcome B.** An operator acceptance was **supplied** and was **not recorded**.
The condition `ted-database-right-residual-exposure-accepted` remains
**OUTSTANDING**, `AcquisitionAuthorizationContext` still cannot be built, and
**no verification row was written** — not `SATISFIED`, not any result.

```text
build_authorization('ted-eu', 'local-private-research-v1')
  review conditions not satisfied:
    ted-database-right-residual-exposure-accepted
```

**This is a valid mission result** (§8), and it is not a rejection of the
operator's decision.

---

## 0. The decision, up front

The operator supplied a real, specific and informed acceptance. It names the
profile exactly, names H-36, and says the acceptance is neither a legal guarantee
nor a resolution. Nothing about it is vague and nothing about it is in doubt.

It is also **materially shorter** than the acknowledgement the condition
requires. Three of the seven items in
[`ted-eu-authorization-bootstrap-v1.md`](../data/ted-eu-authorization-bootstrap-v1.md)
§6.2 are absent entirely, and one of the three is the item that gives the
acceptance a **boundary** — the clause saying it falls if bounded queries,
acquisition-time minimisation or the absence of redistribution stops being true.

**The tempting inference was available and was refused.** Somebody who names
H-36 and disclaims legal guarantee has plainly engaged with the substance, and it
would be easy to conclude they must have read the risk document and would agree
to the rest. Drawing that conclusion would be **this repository supplying the
part of an acceptance the human did not supply** — precisely what a
`HUMAN_CONFIRMATION` condition exists to make impossible, and precisely what §1
and §8 of the brief forbid.

---

# The §25 questions

## What exact operator statement was supplied?

Verbatim, in the original French, which is authoritative:

> J’accepte le risque résiduel TED pour `local-private-research-v1`, en
> comprenant que l’utilisation 100 % locale réduit l’exposition mais ne
> constitue pas une garantie juridique ni une résolution de H-36.

And as supplied in English alongside it:

> I accept the residual TED risk for `local-private-research-v1`, understanding
> that 100% local use reduces the exposure but does not constitute a legal
> guarantee or a resolution of H-36.

## Was it treated as human-supplied rather than model-generated?

**Yes.** It is reproduced unchanged, in both languages, in
[`ted-eu-operator-acceptance-pending-v1.md`](../data/ted-eu-operator-acceptance-pending-v1.md)
§1, and nothing rewords it into stronger or weaker language.

A test asserts the French is present **character for character**, including the
U+2019 apostrophes the operator used. That assertion earned its place
immediately: the first draft of the document had silently substituted ASCII
apostrophes, which is the smallest possible version of rewriting somebody's
statement and exactly the habit that must not start here.

## Was the canonical seven-part acknowledgement required by the actual contract?

**The seven-part text is not itself the contract. The condition is**, and it is
versioned data on TED local review v2:

> A named operator **has read `ted-eu-local-official-route-readiness-v1.md`** and
> **accepted the residual, unresolved database-right exposure for bounded
> queries** under this profile.

It is a **conjunction**, and §6.2 renders it as the acknowledgement an operator
records. The comparison was made against that conjunction and against what each
item *does* — never against a count of seven.

Nothing in code validates the content of a human confirmation. The database
enforces only that a `SATISFIED` verification row exists before the boolean can
be set. So the contract that decides this is the condition's own text, read as
written.

## Was the supplied statement sufficient?

**No.** The item-by-item comparison is in the pending document §4. In summary:

| | |
|---|---|
| **Supplied** | the risk is accepted · scoped to `local-private-research-v1` · not a legal guarantee · **H-36 not resolved by it** · local reduces exposure without eliminating it |
| **Absent** | has read the two documents (item 1) · the four bases, none a database-right grant (item 4) · **the boundary clause** (item 5) · the A/B split of H-36 (items 2–3) · no lawyer reviewed it (item 6) · review version 2 and *nothing else* (item 7) · the exclusion paragraph |

Two absences are load-bearing rather than ceremonial.

**Item 5 is the boundary.** An acceptance that does not state what it depends on
is one that survives the disappearance of what it depended on.

**Item 1 is the informed half of the conjunction.** The readiness document is
where the specific limits live — bulk XML blocked, `ted-csv` blocked, coverage
from 1 March 2023, the authenticity limit that makes every future claim *"TED
reported…"*, the monetary semantics that must not be flattened. Accepting a risk
whose shape one has not confirmed reading is a different act from the one the
condition describes.

The house rule settles the rest: **uncertainty is never permission**, and a
two-part requirement with one part unaddressed is not satisfied.

## Was a human verification recorded?

**No.** The registry holds **zero** verification rows for `ted-eu`, at any
review version, of any result.

## Against which source · use profile · review version · condition?

None. Had the statement been sufficient, the row would have attached to
`ted-eu` · `local-private-research-v1` · local review **v2** ·
`ted-database-right-residual-exposure-accepted`.

## What actor/verifier identifier was recorded?

**None.** No identifier was chosen and none was invented. `local-operator` was
available as the neutral identifier §7 permits, and was not used, because there
was nothing to record.

## Was H-36A changed? Was H-36B changed?

**No, and no.** H-36A remains **NOT ESTABLISHED**; H-36B remains **NOT
ADDRESSED** for broad corpus extraction, under both profiles. An acceptance could
not have changed either — it is a decision to proceed with uncertainty, never a
finding that the uncertainty is gone.

## Was any legal clearance claimed?

**No.** No document produced by this mission uses the phrase except to deny it,
and none states `AUTHORIZATION_READY`. A test asserts both.

## Did the acceptance transfer to `commercial-multi-tenant-research-v1`?

**No — and it could not have, even if recorded.** The commercial review does not
carry the condition an acceptance would clear. Profile scoping is structural, not
conventional: a verification row hangs off a condition, the condition hangs off
exactly one review, and that review names exactly one `assessed_use_profile`.
`build_authorization('ted-eu', 'commercial-multi-tenant-research-v1')` still
refuses with `REQUIRES_REVIEW`, and the refusal does not mention the residual
condition at all.

## Did it authorize bulk XML · historical TED CSV · redistribution · training · embeddings?

**No, to all five, and none of them was ever reachable from a risk acceptance.**

| | |
|---|---|
| `ted-bulk-xml` | refused **by name** at the route gate; absent from `context.access` |
| `ted-csv-historical` | excluded dataset family; `require_dataset_family` denies an unclassified resource too |
| redistribution | `raw_redistribution = false` on the local profile; the review assesses it `NOT_PERMITTED` |
| model training | `model_training = false` on **both** registered profiles |
| embeddings | `embeddings = false` on both, and blocked independently by D-12 |

## Are route restrictions unchanged? Is personal-data minimisation unchanged?

**Both unchanged, and asserted rather than assumed.** The route gate still
accepts `ted-search-api` and `ted-open-data-sparql`, refuses `ted-bulk-xml` by
name, refuses an unreviewed route and refuses acquisition that names none. The
field gate still accepts the authorised set and refuses every excluded
natural-person field — alone and hidden among authorised fields — plus an
unreviewed field and an unstated selection.

The other three conditions remain `SATISFIED`, so nothing regressed while this
one stayed outstanding.

## Can `AcquisitionAuthorizationContext` now be built?

**No.** One condition, named in the refusal, asserted as the complete tuple.

## If yes, what routes does it contain? Does it exclude `ted-bulk-xml`?

Not applicable — no context was built. What it **would** carry is already
established and tested at the level below: `_reviewed_access` against the real
TED record yields exactly `{ted-search-api, ted-open-data-sparql}` and excludes
`ted-bulk-xml`, which the registry does record as a real route.

## Is TED now AUTHORIZATION_READY for `local-private-research-v1`?

**No.** It remains `APPROVING_BUT_NOT_ELIGIBLE`.

## Were any collectors implemented? Was any TED procurement data collected?

**No, and no.** No TED module, HTTP client, SPARQL client, parser, normalizer or
worker — asserted against the file tree. No network call of any kind: this
mission read a database and wrote documents.

## Was the local research database unchanged?

**Yes.** Observed with `row_security = off`, before and after:

| | Before | After |
|---|---|---|
| RawRecords · NormalizedRecords · Signals · Claims · ClaimRevisions · Evidence | 0 | 0 |
| ReliabilityAssessments · Opportunities · Embeddings | 0 | 0 |
| **TED rows** | **0** | **0** |
| **`ted-eu` verification rows** | **0** | **0** |

Per §21 these are this machine's counts, not the historical
12 / 12 / 7 / 7 / 7 from the PostgreSQL those missions ran in. **No research data
changed during this mission**, which is the assertion that matters.

## Is the full test suite green?

See §3.

## Is the next mission TED Official Search API Collector V1?

**No.** §26's condition is not met: the acceptance was not validly recorded and
no context builds.

**The exact remaining blocker:** the operator records the acknowledgement in
[`ted-eu-operator-acceptance-pending-v1.md`](../data/ted-eu-operator-acceptance-pending-v1.md)
§7. Then this mission can be re-run to write the single row, and the collector
mission follows that.

---

## 1. What §17 turned out to be — answered, not changed

The brief asked whether a verification attached to local review v2 would
automatically satisfy a future v3, and told me to prefer fail-closed without
changing architecture unless a real bug appeared.

**No bug. It is already fail-closed, structurally.**
`registry.source_review_conditions` is keyed `(review_id, condition_key)` and the
row id derives from the review version, so each review version owns **its own
condition rows**. The database confirms it for TED today:

```text
local-private-research-v1  v1  ted-database-right-residual-exposure-accepted  (superseded)
local-private-research-v1  v2  ted-database-right-residual-exposure-accepted  (current)
```

Two separate rows, two separate ids. A v3 would create a third with
`satisfied = FALSE`, and a v2 acceptance could not reach it. A test asserts the
two rows are distinct rather than asserting the intent.

**This is why §6.2's items 5 and 7 are worth recording for what they say, not for
what they enforce.** Review-version scoping, profile scoping and every route,
field, redistribution, training and embedding restriction are guaranteed by the
machinery. What the operator's words add is evidence of what they understood
they were accepting — which is the whole content of a human confirmation, and
the reason it cannot be shortened by pointing at the machinery.

## 2. Three things worth recording

**The refusal cost one round trip; the alternative cost the mechanism.** The
whole point of `HUMAN_CONFIRMATION` is that no part of it is supplied by the
system. A mission that accepted a shorter statement because the shorter statement
seemed sincere enough would have established that the acknowledgement set is
advisory — and the next such decision would be easier, and the one after that
easier still.

**Refusing is not dismissing, and the document says so first.** The pending
record opens by stating that this is not a rejection of the operator's decision,
then credits the four things the statement genuinely establishes before listing
what is missing. A refusal that reads as a rebuke teaches people to route around
the gate; one that shows exactly how close they are teaches them to finish.

**A verbatim quotation that normalises punctuation is not verbatim.** The first
draft of the pending document substituted ASCII apostrophes for the operator's
U+2019. Nothing turned on it, and that is the point: the habit of quietly
improving somebody's recorded words is the same habit that later adds an
acknowledgement they did not make. The test now asserts the exact codepoints,
normalising across the blockquote's line breaks but never across its characters
(`testing-strategy.md` §39).

## 3. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | **pass** — 515 tests across 8 packages |
| Pytest suites | **pass** — all suites across 7 packages; database unchanged by the run |
| All seven validators | **pass** |
| Contract generation `--check` | current |
| Generated catalog documents `--check` | current |
| `ruff format` / `ruff check` | **pass** |
| `mypy` | **pass** |
| New tests | 34 in `test_ted_operator_acceptance.py` |

## 4. What this mission changed

| | |
|---|---|
| **Registry** | **nothing.** No verification, no condition, no boolean |
| **Catalog / compliance** | **nothing** |
| **Code** | **nothing** |
| **Documents** | `ted-eu-operator-acceptance-pending-v1.md` (new); readiness and `docs/data/README.md` updated to state the actual result |
| **Tests** | `test_ted_operator_acceptance.py` |

`ted-eu-operator-risk-acceptance-v1.md` was **not** created, and a test asserts
its absence: §23 permits exactly one of the two documents, and it is the pending
one.

## 5. Where this leaves TED

**One sentence short of ready, and the sentence has to come from a person.**

Every objective property is verified. Every restriction holds. The gate refuses
for exactly one reason, names it, and will keep naming it until an operator
records the acknowledgement in full.

That is the design working, and it is worth more than a collector one mission
earlier.

---

# Completion — the acknowledgement was supplied in full, and recorded

**Second run, same mission.** The sections above are the record of the first,
and they are **not rewritten**: the refusal is why the acknowledgement that
follows is the complete one.

**Outcome A.** One `HUMAN_CONFIRMATION` row was written.
`AcquisitionAuthorizationContext` **builds**. **H-36A and H-36B remain open.**

## C1. The new statement was assessed independently

Not carried forward from the previous refusal (§2 of the brief), and not
approved because it was longer. Each item of the condition and of
[`ted-eu-authorization-bootstrap-v1.md`](../data/ted-eu-authorization-bootstrap-v1.md)
§6.2 was checked against what the operator actually wrote:

| §6.2 | First statement | Second statement |
|---|---|---|
| 1 — has read both documents in full | absent | **supplied** — *"J’ai lu intégralement…"* |
| 2 — H-36A `NOT ESTABLISHED`, subsists and who holds it | H-36 named, no A limb | **supplied**, both halves |
| 3 — H-36B `NOT ADDRESSED` for broad corpus extraction | no B limb | **supplied**, granted or waived |
| 4 — four bases, none a database-right grant | absent | **supplied**, with one hedge, §C2 |
| 5 — bounded queries, minimisation, no redistribution, **and falls with them** | absent | **supplied**, including the falls-with clause |
| 6 — not a legal validation, no lawyer, resolves neither limb | partial | **supplied**, all three |
| 7 — `ted-eu`, `local-private-research-v1`, **review version 2**, nothing else | profile only | **supplied**, including the version |
| exclusions | absent | **supplied**, complete |

The condition's own *"for bounded queries"* qualifier is met by item 5's
*"requêtes bornées et ciblées"*.

**Sufficient.** Every element present, in the operator's own words.

## C2. One wording difference, kept rather than smoothed

Item 4 asks that none of the four instruments **is** a database-right grant. The
operator wrote that none constitutes **"à lui seul"** an **"explicite"** grant.

The hedge is **kept as written** and recorded in
[`ted-eu-operator-risk-acceptance-v1.md`](../data/ted-eu-operator-risk-acceptance-v1.md)
§1. It changes nothing operative — the acceptance clause states the exposure is
*résiduel et non résolu*, which is coherent only if nothing granted the right —
and the record must carry the operator's words rather than the template's.

Rewriting a hedge into the stronger canonical phrasing would have been the same
act as inventing an acknowledgement, one degree smaller.

## C3. What was recorded

| | |
|---|---|
| Source · profile · review | `ted-eu` · `local-private-research-v1` · **v2** |
| Condition | `ted-database-right-residual-exposure-accepted` |
| Kind · result | `HUMAN_CONFIRMATION` · **`SATISFIED`** |
| Actor | `local-operator` — the neutral identifier; **no legal name invented** |
| Verifier version | `acknowledgement-v1` — which TEXT was signed, not a program version |
| Recorded at | 2026-08-31T20:09:29Z |
| Reason | the acknowledgement, **verbatim**, in French |
| Rows written | **exactly one**, and a test asserts there is no second |

Written through `registry.source_condition_verifications` and nothing else. **No
CLI verb was built** — Mission 1.15.6 refused to build one and that decision
stands; the row came from a one-off act that is not part of the repository.

## C4. The authorization

```text
build_authorization('ted-eu', 'local-private-research-v1')  ->  CONTEXT

  use profile   local-private-research-v1
  review        v2  APPROVED_WITH_CONDITIONS
  routes        ted-open-data-sparql, ted-search-api
  ted-bulk-xml  ABSENT
  preferred     ted-search-api
```

**Blocked and asserted:** `ted-bulk-xml` refused by name · `ted-bulk-xml-daily`,
`ted-bulk-xml-monthly`, `ted-csv-historical` excluded · unclassified resource
denied · every natural-person field refused, alone and among allowed fields ·
redistribution `NOT PERMITTED` · training and embeddings false on **both**
profiles · `commercial-multi-tenant-research-v1` still `REQUIRES_REVIEW`, with a
refusal that does not mention this condition.

## C5. Two findings the mission surfaced, and neither was fixed here

**The recorded decision and the live verifiers never meet.** No shipped command
produces a complete verification set for a source that has a human condition:
`verify_source` answers `UNKNOWN` for it **by design and always**, so
`build_authorization` with no arguments still refuses; the SQL view sees the
recorded acceptance but not the three capability results, which were never
recorded. The context in §C4 was built by supplying the union — which is what the
`verifications` parameter exists for — and **no production caller does that
today**.

**And `verify --apply` would erase the acceptance.** Confirmed empirically in a
rolled-back transaction: `verify_source` yields `UNKNOWN` for the human
condition, `record_verifications` writes `satisfied = FALSE` for any
non-`SATISFIED` result, and the boolean goes from `True` to `False`. Correct for
a capability that stopped holding; destructive for a decision a person made once.

A test asserts this as **current** behaviour so that a future mission which
changes it has to invert the test deliberately rather than discover the change
in production. **Operationally, until then: do not run `verify --apply` for
`ted-eu` under this profile.**

Both belong to the mission that decides how re-verification should treat a human
condition — skip, preserve, or require an explicit withdrawal. §3 of this brief
forbade altering the verification model, and that was the right instruction.

## C6. `AUTHORIZATION_READY` is not `resource_ready`

**TED authorises zero concrete datasets** (`"datasets": []`), so a collector
holding the context would be refused every resource it asked for, for want of a
rights basis and a dataset family. `resource_ready` is **no**, exactly as
Eurostat has been since Mission 1.4 and exactly what Mission 1.9.2 separated the
two facts to make visible.

So Mission 1.15.7's first act is **not** writing a client. It is authorising a
concrete resource — eForms contract notices and contract award notices, from
1 March 2023, through the reviewed routes — with a stated basis, which is a
governance act.

## C7. Research state

| | Before | After |
|---|---|---|
| RawRecords · NormalizedRecords · Signals · Claims · ClaimRevisions · Evidence | 0 | 0 |
| ReliabilityAssessments · Opportunities · Embeddings | 0 | 0 |
| **TED research rows** | **0** | **0** |
| `ted-eu` verification rows | 0 | **1** |

Observed with `row_security = off`. **The single verification row is the only
database mutation this mission made** (§18). Per §21 these are this machine's
counts, not the historical 12 / 12 / 7 / 7 / 7 from another instance.

## C8. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | **pass** — 515 tests across 8 packages |
| Pytest suites | **pass** — all suites across 7 packages |
| All seven validators | **pass** |
| Contract generation `--check` · generated documents `--check` | current |
| `ruff format` / `ruff check` / `mypy` | **pass** |
| Tests in `test_ted_operator_acceptance.py` | **54** |
| First-run assertions | **inverted, none deleted** |
| Mission 1.15.6 assertion inverted | 1 — *no residual acceptance was written* now asserts that any acceptance came from a **person**, not a verifier |
| CI caught | the first version of the new tests asserted the recorded acceptance **unconditionally** and went red on a database that correctly has none — recorded as `testing-strategy.md` §49 |

## C9. Final state

```text
ted-eu + local-private-research-v1 + review v2
  APPROVED_WITH_CONDITIONS
  4 of 4 conditions satisfied
  AcquisitionAuthorizationContext  BUILDS
  AUTHORIZATION_READY

  H-36A           NOT ESTABLISHED
  H-36B           NOT ADDRESSED
  legal clearance NONE
  resource_ready  NO
  bulk XML        BLOCKED
  ted-csv         BLOCKED
  redistribution  BLOCKED
  training        BLOCKED
  embeddings      BLOCKED
  commercial      REQUIRES_REVIEW
  collector       NONE, and none was written
```

**Next: Sprint 1 — Mission 1.15.7, TED Official Search API Collector V1 — Local
Private Research Profile**, not started here. Its first act is §C6's resource
authorisation, and it must settle §C5 before the state recorded today can be
relied on twice.

## C10. Worth recording

**The bar held, and then it was cleared.** The first statement was a real
acceptance of the core risk and was refused for three absences. The second
supplied all of them. That sequence is the mechanism working exactly as
designed — and it is why the refusal document is preserved rather than deleted:
without it, the completeness of the recorded acknowledgement looks like
formality rather than the result of a bar that was actually applied.

**The smallest infidelity was the instructive one.** In the first run, the
"verbatim" quotation had silently substituted ASCII apostrophes for the
operator's U+2019, and a test caught it. In this run, the operator's hedge in
item 4 was kept rather than normalised into the canonical phrasing. The two are
the same discipline at different scales: **the record carries what the person
wrote, not what the template expected them to write.**
