# TED-EU Governing Decision Review V1 — H-34 Closed

**Authoritative.** Mission 1.15.2. The reading of Commission Decision
2011/833/EU, and what it settles.

**H-34 closes PERMITTED.** The Decision defines reuse by *purpose* and says
nothing about *method*, and the machine processing the engine needs — inference,
extraction, classification — falls inside a grant that broad.

**TED stays `REQUIRES_REVIEW`** at review v3, because H-36 does not close. See
`ted-eu-database-right-review-v1.md`.

---

## 0. The document, and how it was reached

| | |
|---|---|
| **Title** | Commission Decision of 12 December 2011 on the reuse of Commission documents (2011/833/EU) |
| **Publisher** | European Commission |
| **CELEX** | 32011D0833 |
| **ELI** | `dec/2011/833/oj` |
| **Official Journal** | L 330, pp. 39–42 — `JOL_2011_330_R_0039_01` |
| **Cellar identifier** | `cb76d4a0-c886-40bd-99d7-8db018a723d0` |
| **Representation read** | PDF, 4 pages, 16,748 characters, Articles 1–13 with recitals 1–9 |
| **Retrieved** | 2026-08-31, Publications Office `opportal-service` download handler |

**The route matters.** EUR-Lex failed again — five representations in Mission
1.15.1 and, this round, the Official Journal L 330 full-issue HTML too, which
had not been tried. `publications.europa.eu/resource/celex/32011D0833` redirects
to an RDF metadata object rather than operative text.

What worked was the **Publications Office's own Cellar repository**, addressed by
the Cellar identifier that the Publications Office publication record itself
publishes. That is a first-party representation reached by following the
publisher's own identifiers — not a mirror, not an archive, not a third-party
database.

The chain, each link documented:

```text
TED legal notice
    names →  Commission Decision of 12 December 2011 (with its ELI address)
                ↓
Publications Office publication record
    publishes →  Cellar identifier cb76d4a0-…
                ↓
Cellar download handler
    serves   →  the operative text
```

## 1. Scope — and that it reaches TED

**Article 1.** The Decision *"determines the conditions for the reuse of
documents held by the Commission or on its behalf by the Publications Office of
the European Union"*.

**Article 2(1).** It applies to public documents produced by the Commission or
by public and private entities on its behalf *"which have been published by the
Commission or by the Publications Office on its behalf through publications,
websites or dissemination tools"*.

TED is operated by the Publications Office and publishes procurement notices
through a website and dissemination tools. TED's own legal notice names this
Decision as the instrument implementing the reuse policy under which its notices
are reusable. **The link is documentary at both ends.**

### Exclusions — Article 2(2)

The Decision does **not** apply to:

| Excluded | |
|---|---|
| (a) | software, and documents covered by industrial property rights such as patents, trademarks, registered designs, logos and names |
| (b) | documents the Commission cannot allow reuse of *"in view of intellectual property rights of third parties"* |
| (c) | documents excluded from access under Regulation (EC) No 1049/2001 |
| (d) | confidential data as defined in Regulation (EC) No 223/2009 |
| (e) | unpublished ongoing Commission research |

**Every exclusion is a class of *document*.** Not one is a method of use.

**Article 2(4)** adds the only manner-of-use prohibition in the whole
instrument: *"Nothing in this Decision authorises reuse of documents in a manner
calculated to deceive or to defraud."*

## 2. The definition — the heart of H-34

**Article 3(2):**

> *"'reuse' means the use of documents by persons or legal entities of
> documents, for commercial or non-commercial purposes other than the initial
> purpose for which the documents were produced. The exchange of documents
> between the Commission and other public sector bodies which use these
> documents purely in the pursuit of their public tasks does not constitute
> reuse."*

Read it for what it does and does not do:

- **It defines reuse by PURPOSE.** *Use … for purposes other than the initial
  purpose.* The test is what the use is *for*, not what is done to the document.
- **It enumerates no acts.** There is no list of copying, adaptation,
  transformation or analysis that a use must fall within. Method does not enter
  the definition.
- **It carves out exactly one thing** — inter-public-body exchange in pursuit of
  public tasks — which is not us.

**Article 3(1)** defines a document as *"any content whatever its medium"* and
*"any part of such content"*.

## 3. The grant

**Article 4:**

> *"All documents shall be available for reuse: (a) for commercial or
> non-commercial purposes under the conditions laid down in Article 6; (b)
> without charge …; and (c) without the need to make an individual
> application …"*

**Article 6(1):** documents *"shall be made available for reuse without
application unless otherwise specified and without restrictions or, where
appropriate, an open licence or disclaimer setting out conditions explaining the
rights of reusers."*

**Article 6(2):** conditions *"shall not unnecessarily restrict possibilities for
reuse"* and may include:

| | |
|---|---|
| (a) | the obligation for the reuser to acknowledge the source |
| (b) | **the obligation not to distort the original meaning or message** |
| (c) | the non-liability of the Commission |

**None of the three concerns how a document may be processed.**

**Article 9:** reuse is *"in principle free of charge"*.
**Article 11:** conditions must be non-discriminatory between comparable
categories of reuse, and no exclusive rights are granted.

## 4. H-34 — resolved, with the reasoning written out

§12 of the mission permits closing without the literal words *machine learning*
if the operative grant clearly covers arbitrary analytical reuse, and requires
the reasoning to be tied to the text. Here it is:

1. **Article 3(2) defines reuse by purpose, not by method.** Reading a
   procurement notice with software to extract the award value is a *use of the
   document for a purpose other than the initial one* — the initial purpose
   being the publication of a procurement notice. That is squarely inside the
   definition on its own terms.
2. **Article 4 makes all in-scope documents available for reuse** on exactly that
   footing, for commercial purposes, without charge, without application.
3. **Article 6 constrains conditions rather than methods.** Conditions may not
   *"unnecessarily restrict possibilities for reuse"*, and the three the Decision
   contemplates are attribution, non-distortion and non-liability.
4. **The Article 2(2) exclusions are classes of document.** A reviewer looking
   for a method-based exclusion finds none.
5. **The one manner-of-use prohibition is Article 2(4)** — deception or fraud —
   which is a constraint the engine already meets by construction: an `OBSERVED`
   claim restates what a source reported and is attributed.
6. **The recitals point the same way.** Recital (2) describes *"unprecedented
   possibilities to aggregate and combine content from different sources"*;
   recital (3) treats public-sector information as a source of growth through
   *"value-added products and services"*; recital (4) says Commission documents
   *"could be reused in added-value information products and services"*.

**This is not silence about machine learning.** It is a grant whose operative
term is defined broadly enough that the method of use does not enter — which is
a different thing, and the thing §12 asks for.

### What was NOT concluded

| Activity | Finding |
|----------|---------|
| **Inference, extraction, classification** | Within the grant. This is the engine's assessed need |
| **Model training** | **Not assessed and not authorised by this review.** The Decision does not distinguish methods, so a broad reading would reach training too — but training raises Article 2(2)(b)'s third-party-rights exclusion in a materially different form, because a trained artefact may embody material the Commission was never in a position to license. The engine does not need it (§13) |
| **Embeddings** | Same legal character as other computational processing, and **not assessed for implementation**. D-12 blocks it independently, and §14 forbids letting an inference decision be inherited silently |
| **Generative output** | Not assessed; not required by any current or planned stage |

The review records `model_processing` as `PERMITTED` with a **condition scoping
it to inference, extraction, classification and structured analysis**. A single
field carries the finding; the condition carries its boundary.

## 5. New conditions the Decision imposes

Three, added at review v3 alongside every condition from v1 and v2:

**Article 6(2)(b) — do not distort the original meaning or message.** This is
the condition with the most direct bearing on the claim layer. An `OBSERVED`
restatement of an award notice must say what the notice says, and a derived
signal must not be presented in a way that changes what the procurement record
means. The interpretation contract already requires this epistemically; the
Decision makes it a legal obligation as well.

**Article 2(4) — no reuse calculated to deceive or defraud.**

**Article 6(2)(c) — the Commission accepts no liability for consequences of
reuse.** Read with TED's existing authenticity condition: a claim derived from a
notice is a claim about what TED published, never a warranted statement about
the underlying contract.

## 6. What this does not do

**It does not make TED usable.** All six load-bearing activities are now
positively granted and the source is still `REQUIRES_REVIEW`, because the
remaining question is not an activity in the matrix — it is whether a different
body of rights sits over the same data (H-36).

**It does not authorise a collector.** And the unresolved question bears
specifically on the bulk route a collector would use.
