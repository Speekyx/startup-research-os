# Mission 1.15.1 — TED-EU Reuse & Machine-Learning Processing Resolution

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.1` · **Scope:** one
open question, from first-party evidence.

**Outcome C — H-34 remains OPEN.** TED-EU stays `REQUIRES_REVIEW` at review v2.
No activity assessment moved. Nothing was collected, built, claimed or scored.

The governing instrument is now **named and proven to apply**. Its text returned
an empty body at five first-party addresses.

---

## 0. The shape of the finding

The mission set out to answer whether TED's reuse grant covers machine-learning
processing. It found something more specific than a yes or a no:

> The grant says notices *"can be freely reused"*. The operative word is
> **reused**, and its scope is defined in an instrument that could not be read.

That is a different situation from silence, and a worse one to build on.

---

# The questions (§36)

## What exactly was H-34?

> Does the EU Publications Office / TED reuse framework permit machine-learning
> processing of reused TED notices for Startup Research OS's assessed use case?

Mission 1.15 recorded seven of TED's activities as `PERMITTED` on one retrieved
sentence and `model_processing` as `NOT_ADDRESSED`. That single gap is the whole
distance between TED and an approving verdict.

## Which document legally governs TED data reuse?

**Commission Decision 2011/833/EU of 12 December 2011 on the reuse of Commission
documents**, published in Official Journal L 330.

## Is that document first-party?

Yes. Published by the European Commission on EUR-Lex, at the canonical ELI
address `https://eur-lex.europa.eu/eli/dec/2011/833/oj`.

## Does it apply specifically to TED?

**Yes, and the link is proven rather than assumed** — which §5 required. TED's
own legal notice states:

> *"The European Commission's reuse policy is implemented by the Commission
> Decision of 12 December 2011 on the reuse of Commission documents."*

and links that ELI address. This is not a generic EU open-data statement
presumed to cover TED; it is TED naming its own instrument.

The TED Developer Docs were also retrieved and carry no licence of their own,
linking back to the same legal notice — which establishes that the legal notice
is *the* governing statement on the TED side rather than one of several.

## Is commercial reuse permitted?

**Yes**, from the TED legal notice directly:

> *"Unless otherwise noted, the procurement notices published in the Supplement
> to the Official Journal of the European Union can be freely reused, for
> commercial or non-commercial purposes."*

Unchanged from Mission 1.15.

## Is storage permitted?

`PERMITTED`, carried forward from Mission 1.15 unchanged. Bulk daily and monthly
XML packages are published for download without signing in.

## Are derived analytics permitted?

`PERMITTED`, carried forward unchanged.

## Is automated processing permitted?

`PERMITTED` in the sense of automated *access* — the bulk packages and the
documented read-only search API are the intended reuse routes.

Automated processing in the sense of **computational analysis of the content** is
the H-34 question, and it is not answered.

## Is text/data mining addressed?

**No.** Not in the TED legal notice, not in the Publications Office copyright
notice, not in the TED Developer Docs. The instrument that might address it could
not be read.

## Is machine-learning inference permitted?

**Unknown.** `NOT_ADDRESSED`.

§7 permits closing H-34 without the exact phrase "machine learning" *if a broader
legal permission clearly and explicitly covers the activity*, and forbids
inferring permission from silence. Neither branch applies here:

- the grant is not explicit about computational analysis;
- and the problem is not silence. The grant uses a **defined term** — "reuse" —
  whose definition lives in the Decision, and that text returned an empty body
  five times.

Reading the grant as covering ML inference would mean assuming a definition from
an unread document. That is a weaker basis than inferring from observed silence,
because silence is at least a fact one has established.

## Are embeddings addressed separately?

**Not addressed, and deliberately not folded into the inference question.** D-12
remains open and nothing was implemented. §15 is explicit that a future embedding
use must not silently inherit an ML-inference decision if the legal text
distinguishes them — and since the legal text is unread, there is nothing to
inherit.

## Is model training addressed separately?

**Not addressed, and not part of the assessed need.** §14: the engine needs
inference, extraction and classification before it needs training, and training
uncertainty must not block inference where the framework treats them separately.
No document retrieved mentions training.

## Are database rights addressed?

**No — and this is the finding nobody had asked for.** Recorded as **H-36**.

TED is a database, and the documented reuse route is bulk daily and monthly XML
packages: extraction and re-utilisation of substantial portions. The sui generis
database right is independent of copyright, and a reuse grant framed around
*documents* does not automatically carry it.

Nothing retrieved addresses databases, extraction or re-utilisation. Mission
1.15's review recorded seven activities as `PERMITTED` on one sentence and did
not ask this.

**It bears on `automated_access` (bulk) and `redistribution` rather than on
`model_processing` — so it could block TED even if H-34 closes favourably.**

Recorded as a new open question rather than used to downgrade Mission 1.15's
findings: a question nobody has answered is not evidence that an earlier review
was wrong, and rewriting a prior review on a suspicion is what the append-only
rule exists to prevent.

## What attribution is required?

Unchanged from Mission 1.15: CC BY 4.0 for reused editorial material, with
appropriate credit and changes indicated. SIMAP metadata is CC0 1.0. The TED and
SIMAP logos require the Publications Office's prior consent.

**Added in v2:** industrial property — patents, trademarks, registered designs,
logos and names — is excluded from the reuse policy and not licensed.

## What personal data appears in TED notices?

Contact details of contracting authorities and successful tenderers: names,
addresses, email addresses, telephone and fax numbers. Retained ten years on the
TED website, then archived.

**Added in v2**, from the legal notice's reuse section: additional rights may
need clearing where content depicts identifiable private individuals or includes
third-party works. **The reuse grant is not a blanket grant over everything
inside a notice**, which makes minimisation a compliance requirement rather than
a preference.

## What fields must Startup Research OS discard?

Unchanged and not weakened.

| Keep | Discard |
|------|---------|
| Award value, currency | Natural-person name |
| Buyer organisation name | Personal email |
| Supplier organisation name | Telephone, fax |
| CPV classification | Personal address |
| Contract dates, notice id | The entire contact block |

H-34 concerns reuse and ML processing. It has never concerned permission to
ingest additional personal data, and nothing here changed that.

## Is the authenticity condition unchanged?

**Yes.** Only electronically signed notices published in the Official Journal
Supplement are authentic; online documents are *"not necessarily exact
reproductions"*. Any future claim must be attributed to TED's published notice
and must never silently assert it is the legally authentic contract.

Asserted by test, because a mission about reuse rights is exactly where an
unrelated condition gets weakened incidentally.

## Did TED's verdict change?

**No.** `REQUIRES_REVIEW`, as before.

## What is its new review version?

**2.** Appended, not rewritten. Every activity assessment is byte-identical to
v1 — asserted by `v1.assessments == v2.assessments`.

The version exists because the *evidence base and the open questions* changed
materially, on the Bluesky-v2 precedent from Mission 1.15: a review may move from
"we do not know what governs this" to "this named document governs it and could
not be read" while the verdict holds.

## Is H-34 CLOSED or OPEN?

**OPEN**, refined.

Before: *does the Publications Office's reuse decision, or another first-party
instrument, address machine-learning processing?*

Now: *retrieve Commission Decision 2011/833/EU and establish the scope of "reuse"
as it defines the term.*

The first is research. The second is one retrieval from an environment that
renders EUR-Lex.

## If CLOSED, what evidence closed it?

Not applicable.

## Is TED collector-eligible?

**No.** It does not pass the eligibility gate, because it is not approving.

## Can AcquisitionAuthorizationContext be built?

**No.** A context requires an approving source with satisfied conditions.
`sros-source readiness` reports TED as failing the eligibility gate.

That is the gate working, not a limitation to engineer around.

## What exact resource is authorized?

**None.** §22's narrowest-scope exercise applies only under Outcome A. No
resource was authorised, and none should be until the reuse scope is established
— including because H-36 bears specifically on whether *bulk* access is within
the grant.

## What blockers remain?

| Id | Blocker |
|----|---------|
| **H-34** | Commission Decision 2011/833/EU is unread. Its definition of "reuse" determines the scope of the grant |
| **H-36** | Whether the grant reaches the sui generis database right, given bulk extraction |
| — | Documented rate limits for the TED search API remain unestablished |

## Was any collector implemented?

**No.** `IMPLEMENTED_COLLECTORS` and `IMPLEMENTED_NORMALIZERS` do not contain
`ted-eu`; asserted by test.

## Was any TED research data collected?

**No.** Legal and policy documents were retrieved — that is review work.
Procurement notices are research data and none was fetched.

## Were RawRecords created?

**No.** Asserted live: zero rows in `acquisition.raw_records` and
`acquisition.normalized_records` with `source_id = 'ted-eu'`.

## Were Claims or Evidence generated?

**No.** No policy research was converted into a Claim. Claims 7, Evidence 7 —
the same seven as before.

## Were reliability assessments created?

**No.** `epistemic.reliability_assessments` = 0. Source review asks *may we use
this*; reliability review asks *how dependable is this measurement*. Different
processes.

## Was scoring performed?

**No.** No EvidenceScore, no OpportunityScore, no WTP score, no numeric source
priority. The priority ranking remains ordinal buckets with stated reasoning.

## Did the existing 12 / 12 / 7 / 7 / 7 remain unchanged?

**Yes**, asserted live and by the pytest post-suite check.

| Table | Count |
|-------|------:|
| `acquisition.raw_records` | 12 |
| `acquisition.normalized_records` | 12 |
| `nlp.signals` | 7 |
| `research.claims` | 7 |
| `research.claim_revisions` | 7 |
| `scoring.evidence` | 7 |
| `epistemic.reliability_assessments` | 0 |
| `research.opportunities` | 0 |
| `nlp.embedding_provenance` | 0 |

Verdict distribution unchanged: `APPROVED_WITH_CONDITIONS` 5, `REQUIRES_REVIEW`
13, `RESTRICTED` 8, `PROHIBITED` 3. 29 sources.

## If TED becomes approving, is Mission 1.15.2 safe to implement the first TED collector?

**It has not become approving, so the question is conditional — and the condition
is not only H-34.**

If a future retrieval closes **both** H-34 and H-36 favourably, TED would become
`APPROVED_WITH_CONDITIONS` subject to the five conditions on v2 being
representable in compliance configuration. A collector mission would then be
reasonable, and would need first:

- the narrowest authorised resource defined (§22) — award notices, not all
  Publications Office data;
- a minimisation profile that drops the contact block, verifiable rather than
  intended;
- the response contract established for the bulk XML packages;
- the monetary field semantics established (§24) — an amount actually reported
  is not an estimated value, a framework maximum, a lot value or a budget, and
  flattening them into "paid" would be the conflation that made TED worth
  registering.

**If H-34 closes and H-36 does not**, bulk access specifically is in question and
the collector design changes, so the answer is not "yes with a caveat" — it is a
different mission.

## If TED stays blocked, what is the next best WTP route?

**`usaspending`, and it is materially weaker.**

Same transaction class — US federal contract and grant awards — but no licence or
terms document could be retrieved from three first-party locations (H-35). Its
DATA Act sentence establishes that the data must be publicly *accessible*, which
is a statement about publication rather than a grant of reuse rights.

**Beyond those two, there is no third route.** The demand-side coverage report
records willingness to pay as having had *no registered candidate at all* before
Mission 1.15. TED and USAspending are the whole of it.

The honest ordering: retrieve the Decision (answers H-34 and probably H-36 for
TED), and if that fails, retrieve a licence for USAspending. Both are document
retrievals from an environment with better network access, and neither is
engineering work.

---

## 1. What was retrieved

| Document | Outcome |
|----------|---------|
| TED and SIMAP legal notice, reuse section | **Retrieved.** Names the governing instrument; adds two conditions |
| TED Developer Docs | **Retrieved.** No licence of its own; links back to the legal notice |
| Publications Office copyright notice | **Retrieved.** CC BY 4.0 for its website's publications; silent on TDM, ML and automated processing |
| Commission Decision 2011/833/EU — ELI URL | Empty body |
| — ELI English URL | Empty body |
| — CELEX text URL | Empty body |
| — CELEX HTML URL | Empty body |
| — Official Journal L 330 PDF | Empty body |
| `data.europa.eu/en/dataset-legal-notice` | HTTP 404 |

**No mirror, cached copy, archive or third-party transcription was used.**

A search restricted to EU domains returned a summary *describing* the Decision's
articles — including apparent statements about what reuse means. **It was not
treated as evidence and no part of this review rests on it.** §4 is unambiguous,
and this was the one thing in the mission that would have closed the question if
the rule were relaxed.

## 2. What the tests protect

31 tests, none of which contacts a network. The ones worth naming:

- **the retrieval failure is stored as structured evidence** —
  `section_reference = "Retrieval failure"`, "empty body" in the finding. A
  citation normally claims somebody read the document; here it must claim the
  opposite, and only a field does that reliably;
- **no evidence URL is a search engine**, asserted over the recorded URLs;
- **`v1.assessments == v2.assessments`** — a re-review that could not close its
  question must not quietly move findings it did not re-establish;
- **five granted still does not make six**, asserted against the exact granted
  and unaddressed sets;
- **every v1 condition survives into v2**, with the personal-data risk and
  identifier-discard flags pinned.

Recorded as `testing-strategy.md` §35.

## 3. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | 515 tests, 8 packages, pass |
| Pytest suites | 7 packages, pass; database unchanged across 24 tenant and 16 global tables |
| `validate_source_registry` | pass — 29 sources, **42 evidence records**, 0 warnings |
| `validate_schema` · `validate_claims` · `validate_signals` · `validate_normalization` | pass |
| `validate_compliance_capabilities` · `validate_evidence_aggregation` | pass |
| Generated catalog documents `--check` | current |
| New tests | 31 |
| `ruff` / `mypy` | pass |

## 4. The thing worth remembering

The project wants TED to work. It would be the first transaction-class evidence
the portfolio has ever held, and willingness to pay is the largest gap in the
product.

**That had zero effect on the review**, and the mission brief was right to say so
twice. The temptation was concrete rather than abstract: a search result
containing what looked like the answer, one relaxation of one rule away from
closing the question in the direction everybody wanted.

What the mission produced instead is smaller and true: a named document, a
recorded failure to read it, and a second question nobody had thought to ask.
