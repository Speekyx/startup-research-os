# Mission 1.15.2 — TED-EU Governing Decision Retrieval & Database-Right Resolution

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.2` · **Scope:** two
open questions, from the operative legal text.

**H-34 — CLOSED PERMITTED.** The Decision was retrieved and read in full. Reuse
is defined by *purpose*, not by *method*.

**H-36 — NOT CLOSED.** The same text contains nothing about database rights.

**TED-EU stays `REQUIRES_REVIEW` at review v3.** All six load-bearing activities
are now granted, and the source is still blocked.

---

## 0. The shape of the outcome

This is the uncomfortable one:

```text
automated_access     PERMITTED        commercial_use     PERMITTED
api_use              PERMITTED        storage            PERMITTED
derived_analytics    PERMITTED        model_processing   PERMITTED   ← H-34 closed

verdict                                                  REQUIRES_REVIEW
```

**The remaining blocker is not an activity in the matrix.** It is whether a
different body of rights — the sui generis database right — sits over the same
data. §24's rule gives `REQUIRES_REVIEW`, and §23 forbids letting the favourable
half overwrite the unresolved one.

---

# H-34

## State

**CLOSED — PERMITTED**, scoped to inference, extraction, classification and
structured analysis.

## Basis

Commission Decision 2011/833/EU, Articles 2, 3(2), 4 and 6, read in full.

## Documents

| | |
|---|---|
| Decision 2011/833/EU | **Retrieved**, Publications Office Cellar, 4 pages, Articles 1–13 |
| Publications Office publication record | Retrieved — supplied the Cellar identifier |
| EUR-Lex representations | Failed again, including the OJ full-issue HTML |

## Reason

**Article 3(2):**

> *"'reuse' means the use of documents by persons or legal entities of
> documents, for commercial or non-commercial purposes other than the initial
> purpose for which the documents were produced."*

The definition is framed by **purpose** and enumerates **no acts**. Extracting an
award value from a notice with software is a use of that document for a purpose
other than the initial one — the initial purpose being publication of a
procurement notice.

Four supporting points, each from the text:

1. **Article 4** makes all in-scope documents available for reuse for commercial
   purposes, without charge, without individual application.
2. **Article 6(2)** says conditions *"shall not unnecessarily restrict
   possibilities for reuse"* and lists three — acknowledge the source, do not
   distort the meaning, the Commission is not liable. **None concerns method.**
3. **Article 2(2)'s exclusions are classes of document** — software and
   industrial property, third-party IP, access-restricted documents, confidential
   statistical data, unpublished research. Not one is a method of use.
4. **Article 2(4) is the only manner-of-use prohibition** in the instrument:
   reuse *"calculated to deceive or to defraud"*. The engine meets that by
   construction — an `OBSERVED` claim restates what a source reported, attributed.

Recitals 2–4 point the same way: *"unprecedented possibilities to aggregate and
combine content"*, public-sector information as a source of *"value-added
products and services"*.

**This is not silence about machine learning.** It is a grant whose operative
term is defined broadly enough that method does not enter — which is what §12
requires for closing without the literal words.

---

# H-36

## State

**NOT CLOSED — Outcome C**, NOT_ADDRESSED / legal review required.

## Basis

The same Decision, read in full and searched term by term.

| Term | Occurrences |
|------|------------:|
| `sui generis` | **0** |
| `extraction` | **0** |
| `re-utilisation` / `reutilisation` | **0** |
| `Directive 96/9` | **0** |
| `mining` | **0** |
| `database` | 2 — **neither relevant** |

The two `database` hits: Article 2(2)(e)'s exclusion for unpublished research,
and an example inside Article 3(6)'s definition of *structured data*.

## Reason

The Decision governs **documents** — Article 1 (*"documents held by the
Commission or on its behalf by the Publications Office"*), Article 2(1), Article
3(1). The collection those documents sit in is never mentioned.

Article 2(2)(a) excludes industrial property *"such as patents, trademarks,
registered designs, logos and names"*. The database right is not in that list and
not elsewhere. **The instrument neither grants over it nor excludes it — it does
not reach it.**

Three reasons not to read the silence as permission:

1. **The maker of the assembled collection is not established.** Notices are
   filed by contracting authorities across the Union.
2. **The Decision enumerates rights it cannot grant over.** An instrument that
   names third-party IP and industrial property as exclusions is not one whose
   silence naturally reads as a grant.
3. **The engine's route is the aggravating case.** Bulk daily and monthly
   packages are the paradigm of repeated, systematic extraction of substantial
   parts. If any use engages the right, this one does.

**One fact cuts the other way and is recorded.** SIMAP *system metadata* is
dedicated to the public domain under CC0 1.0, and CC0 waives sui generis rights
where the dedicator holds them. That shows the Publications Office addresses this
right when it means to — and it applies to metadata, not to the notice corpus.
Reading it across would extend a stated grant past its stated subject.

---

# The remaining questions (§45)

## Was Commission Decision 2011/833/EU successfully retrieved?

**Yes.** Four pages, Articles 1–13, 16,748 characters.

## Which authoritative representation was used?

The **Publications Office Cellar repository**, through the `opportal-service`
download handler, addressed by Cellar identifier
`cb76d4a0-c886-40bd-99d7-8db018a723d0`.

The chain is documentary at every link:

```text
TED legal notice  → names the Decision, with its ELI address
Publications Office publication record  → publishes the Cellar identifier
Cellar download handler  → serves the operative text
```

EUR-Lex failed again on every representation tried, including the Official
Journal L 330 full-issue HTML that Mission 1.15.1 had not attempted.
`publications.europa.eu/resource/celex/32011D0833` redirects to an RDF metadata
object rather than the text.

## What is the Decision's definition of reuse?

Article 3(2), quoted above. **Use of documents for any purpose other than the
initial one, commercial or not.** The single carve-out is inter-public-body
exchange in pursuit of public tasks.

## Does it apply to TED through a proven documentary chain?

**Yes.** TED's legal notice names the Decision; Article 1 covers documents held
by the Commission *"or on its behalf by the Publications Office"*; Article 2(1)
covers documents published through websites and dissemination tools. TED is
operated by the Publications Office. The link holds at both ends.

## Does reuse permit commercial use?

**Yes.** Article 4(a), and Article 3(2)'s definition names commercial purposes
directly.

## Does reuse permit copying/storage?

**Yes**, within a purpose-framed grant that enumerates no acts and excludes no
methods.

## Does reuse permit derived analytics?

**Yes**, on the same basis, reinforced by recitals 2–4 on aggregation,
combination and value-added products.

## Does reuse permit computational analysis?

**Yes.** Method does not enter the definition, and no exclusion is method-based.

## Is text/data mining addressed?

**No** — zero occurrences. It does not need to be: the grant is not
activity-enumerated.

## Is machine-learning inference covered?

**Yes**, for inference, extraction, classification and structured analysis. See
H-34 above.

## Are embeddings covered or still separate?

**Kept separate and not assessed for implementation.** The same legal character
as other computational processing, but D-12 blocks implementation independently
and §14 forbids inheriting an inference decision silently. Recorded as a
condition.

## Is model training covered or still separate?

**Separate. Not assessed and not authorised by this review.**

The Decision does not distinguish methods, so a broad reading would reach
training. It is excluded here deliberately: a trained artefact may embody
material caught by Article 2(2)(b)'s third-party-rights exclusion, which is a
materially different question — and the engine does not need it (§13).

Recorded as a **condition** on v3, because a single `PERMITTED` field cannot
carry a boundary.

## What exactly is H-34's final state?

**CLOSED — PERMITTED**, scoped as above.

## Which evidence establishes it?

The Decision itself: Articles 2, 3(2), 4 and 6, retrieved from the Cellar and
recorded as policy evidence with its section reference and finding.

## Does the Decision address intellectual-property rights?

**Yes, as exclusions.** Article 2(2)(a) excludes software and documents covered
by industrial property rights; Article 2(2)(b) excludes documents the Commission
cannot allow reuse of *"in view of intellectual property rights of third
parties"*. Both preserved as conditions.

## Does it address database rights?

**No.** Zero occurrences of *sui generis*, *extraction*, *re-utilisation* or
Directive 96/9/EC.

## Is the sui generis database right relevant?

**Yes, potentially** — TED is a database and the documented route is bulk
extraction of substantial portions. Whether the right subsists and who holds it
is not established by anything retrieved.

## Does the reuse framework permit extraction/re-utilisation of TED's database?

**Unestablished.** The framework grants reuse of *documents*. Whether that
carries a right in the collection is the open question.

## Does bulk XML change that answer?

**It sharpens it.** Bulk daily and monthly packages are the clearest case of
extracting substantial parts. The search API returns individual notices matching
a query and is less obviously a substantial part — so the two routes have
different exposure, though neither is authorised on current evidence (§29).

**No collector route was forced.** Choosing bulk now because it is convenient
would mean choosing the more exposed route before knowing whether the exposure is
real.

## What exactly is H-36's final state?

**OPEN — NOT_ADDRESSED / legal review required.**

The change from Mission 1.15.1 is real: this is no longer *"the instrument might
address it and we cannot read it"*. The instrument has been read and **does not
address it**. An unknown became an established absence, which is what makes the
next step a legal question rather than another retrieval.

## Which evidence establishes it?

The full text of the Decision, searched term by term, recorded in the v3 evidence
finding.

## Are third-party rights exclusions preserved?

**Yes**, and reinforced: Article 2(2)(a) and 2(2)(b) confirm from the operative
text what Mission 1.15.1 recorded from TED's legal notice.

## Is personal-data minimisation unchanged?

**Yes.** Keep the notice id, award value, currency, buyer and supplier
organisation names, CPV classification and dates; discard the entire contact
block. Asserted by test.

Article 4 also requires the Decision to be implemented *"in full respect of the
rules on the protection of individuals with regard to the processing of personal
data"*.

## Is authenticity unchanged?

**Yes**, and reinforced by Article 6(2)(c)'s non-liability: a claim derived from
a notice is a claim about what TED published, never a warranted statement about
the underlying contract.

## Did TED's verdict change?

**No.** `REQUIRES_REVIEW`, per §24's rule for permitted-plus-unresolved.

## What is its current review version?

**3.** v1 and v2 unmodified; asserted by test.

## What conditions remain?

Nine — five carried forward, four added:

| From | Condition |
|------|-----------|
| v1 | Attribution under CC BY 4.0; logo requires consent |
| v1 | Personal-data minimisation: discard the contact block |
| v1 | Authenticity: only signed OJ notices are authentic |
| v2 | Additional rights may need clearing for identifiable individuals and third-party works |
| v2 | Industrial property excluded and not licensed |
| **v3** | **Article 6(2)(b): do not distort the original meaning or message** |
| **v3** | Article 2(4): no reuse calculated to deceive or defraud |
| **v3** | Article 6(2)(c): the Commission accepts no liability |
| **v3** | Machine processing scoped to inference/extraction/classification; training not authorised, embeddings unassessed |

## Is TED collector-eligible?

**No.** It does not pass the eligibility gate.

## Can AcquisitionAuthorizationContext be built?

**No.** A context requires an approving source.

## What exact TED resource is authorized, if any?

**None.** §28's narrowest-scope exercise applies only if TED becomes approving.

## Are bulk XML and search API treated differently?

**Analysed separately, both unresolved**, with different exposure. See above.

## Were any collectors implemented?

**No.** Asserted by test.

## Was any procurement research data collected?

**No.** Legal document retrieval is review work; procurement notices are research
data and none was fetched.

## Were any RawRecords/NormalizedRecords/Signals created?

**No.** Zero rows with `source_id = 'ted-eu'`, asserted live.

## Were any Claims/Evidence generated?

**No.**

## Were reliability assessments created?

**No.** 0, asserted.

## Were Opportunities created?

**No.** 0.

## Was scoring performed?

**No.**

## Did the existing 12 / 12 / 7 / 7 / 7 remain unchanged?

**Yes**, per the pytest post-suite digest watcher across 24 tenant and 16 global
tables. Verdict distribution unchanged: 5 / 13 / 8 / 3 across 29 sources.

## If both H-34 and H-36 close favourably, is the next mission TED-EU Collector V1?

**They did not both close, so no** — and §41's collector-readiness document was
deliberately not written.

If H-36 later closes favourably, TED would become `APPROVED_WITH_CONDITIONS`
subject to the nine conditions being representable in compliance configuration,
and a readiness document would come first.

## If not, what exact cheapest action remains?

**A first-party clarification from the Publications Office**, then legal review
— in that order:

1. Ask the Publications Office whether it asserts or waives database rights in
   TED, or whether the reuse policy is intended to cover extraction of the
   corpus. It publishes a contact route.
2. Check whether a licence is attached to the bulk packages themselves — the
   data-reuse page carries none.
3. **Legal review** of whether a documents reuse policy carries the database
   right by implication, and whether the right subsists in TED given who
   assembles it.

**This is not engineering work, and it is the first item in the queue a document
search cannot settle** — because the documents have been read.

**USAspending was not re-reviewed** (§43). TED has not reached a dead end; it has
reached a question with a named addressee.

---

## 1. Two things worth recording

**The retrieval succeeded by following identifiers rather than trying harder.**
Mission 1.15.1 attempted five EUR-Lex URL forms and this mission added a sixth,
all empty. What worked was reading the Publications Office's own publication
record, taking the Cellar identifier it publishes, and asking the Cellar for the
document. The lesson is about following a publisher's identifier chain rather
than guessing at URL shapes.

**Seven tests failed when v3 landed, and every one was correct when written.**
Mission 1.15.1's suite asserted `model_processing` was `NOT_ADDRESSED`; Mission
1.15's asserted five granted activities did not make six. Both were true of the
versions they were written against and became false when v3 granted the sixth.

The fix was **pinning, not deleting**: a *finding* is asserted against its
version, a *durable property* against the current review. Deleting them would
have removed the only mechanical guard against v2 being quietly edited later.
Recorded as `testing-strategy.md` §37.

## 2. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | 515 tests, 8 packages, pass |
| Pytest suites | 7 packages, pass; database unchanged across 24 tenant and 16 global tables |
| `validate_source_registry` | pass — 29 sources, 41 evidence records, 0 warnings |
| All other validators | pass |
| Generated catalog documents `--check` | current |
| New tests | 32, plus 7 pinned |
| `ruff` / `mypy` | pass |

## 3. Where TED stands

**Closer, and further.**

Closer: the reuse grant is read, and it is broad. Every activity the engine
performs on collected data is permitted by the instrument that governs it.

Further: the blocker changed kind. It was a document to fetch; it is now a legal
question the documents do not answer. Retrievals are cheap and certain. Legal
questions are neither.

TED remains the portfolio's only route to transaction-class evidence, and its
expected time-to-usable got worse rather than better. That is the finding, and it
is worth more than an approval that would not survive the question nobody had
asked.
