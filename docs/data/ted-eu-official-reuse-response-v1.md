# TED-EU Official Re-use Response V1 — the reply, and what it reconciles

**Authoritative.** Mission 1.45. The Publications Office answered the
clarification request the repository has carried as an unsent draft since Mission
1.15.3, and this document records what the answer says, what it does not say, and
what moved as a result.

**Outcome: `TED_OFFICIAL_REUSE_GUIDANCE_RECONCILED`.**

**The reply is the publisher's stated reuse policy. It is not an adjudication,
not a waiver, and not legal advice** — the TED legal notice disclaims the last of
those about itself in its own words. Nothing below should be read as a legal
guarantee.

---

## 1. The document

| | |
|---|---|
| **Type** | `OPERATOR_CORRESPONDENCE` — first-party written reply |
| **From** | Jose Antonio DOMÍNGUEZ ROJAS |
| **Role** | Head of Sector — Copyright and legal issues |
| **Organisation** | Publications Office of the European Union, Direction D — Corporate Services, D.2 Contracts and Copyright |
| **To** | the operator |
| **Date** | **2026-09-04**, 11:17 |
| **Subject** | Clarification request regarding database rights and reuse of TED procurement data |
| **Case identifier** | **2026-COP-201** |
| **Answering** | the operator's request of **2026-08-31**, 10:57, to `op-copyright@publications.europa.eu` |
| **Artifact** | PDF export of the message thread, 3 pages, 172,677 bytes |
| **SHA-256** | `faee1e541c88bbd254f0660d2ebdb89e70766eb532a2192174e856ec5f922f74` |

`op-copyright@publications.europa.eu` is the address the TED legal notice itself
publishes for copyright issues, and it is how this matter is re-opened: quote the
case identifier back to it. That is why the evidence row is addressed
`mailto:op-copyright@publications.europa.eu` rather than by a URL.

### 1.1 Why the original file is not committed to this repository

**The artifact is retained by the operator outside the repository, and this
document carries its fingerprint instead.** The PDF contains a named official's
direct telephone number and direct email address, and the operator's own personal
email address. This repository is public.

Committing it would publish natural-person contact data — the exact category this
same mission verifies the TED pipeline does not retain. A governance record that
had to breach the minimisation obligation it exists to check would be a poor
record. What is preserved instead is stronger than a copy in one respect and
weaker in none that matters: the **fingerprint** identifies the exact bytes, the
**operative text is transcribed in full** below, and the **case identifier and
mailbox** let anyone re-open the matter with the issuing office.

The original file must not be altered. If it is ever produced, its SHA-256 must
equal the value above.

---

## 2. The reply, verbatim

> Thank you very much for your interest in the TED data.
>
> I can confirm that the Commission's general re-use policy is governed by the
> so-called "Re-use Decision", as you correctly indicate in your email. Under
> this framework, TED notices and metadata may be reused for both commercial and
> non-commercial purposes, provided that the source is acknowledged and according
> to the copyright notice (link). Metadata are dedicated to the public domain
> under CC-0.
>
> Whether or not the European Union asserts copyright over the database should
> not prevent citizens or organisations from reusing the TED data. The way in
> which the data are retrieved is not relevant in this regard.

**The hyperlink behind "(link)" resolves to `https://ted.europa.eu/en/legal-notice`.**
Extracted from the PDF's own link annotations rather than assumed, which matters:
it is what anchors the acknowledgement condition to a specific instrument.

---

## 3. The question that was asked

**The request described this system by name as "a commercial software-as-a-service
application".** That is load-bearing: a permission obtained by describing a
smaller product is a permission for a product we are not building
(`docs/CLAUDE.md` §Source governance), and this request did not describe a smaller
product.

It enumerated the intended use:

- automated retrieval of publicly available TED procurement notices;
- repeated collection through either the official TED bulk downloads or the
  official Search API;
- storage of a minimised subset of procurement information;
- commercial analytical use of that data;
- automated processing, extraction and classification;
- generation of aggregate market intelligence and derived analytical signals.

It stated the retention limit — notice identifier, award value and currency,
buyer organisation, supplier organisation, CPV classification, procurement and
award dates, necessary classifications — and stated that **natural-person contact
information "would not be retained"**. It stated that model training was not
currently intended.

It asked five questions. **Questions 1, 2 and 3 were answered. Questions 4 and 5
were not.**

| # | question | answered? |
|---|---|---|
| 1 | Is a sui generis or other database-level right asserted over the TED corpus? | **obliquely** — see §5 |
| 2 | If so, does the Decision / COM_REUSE authorise repeated extraction and re-utilisation for commercial analytical services including automated machine processing? | **in substance** — reuse is permitted commercially under the Decision |
| 3 | Does the answer differ between bulk downloads and the Search API? | **yes, directly** — retrieval method is not relevant |
| 4 | Is the CC BY 4.0 / COM_REUSE catalogue split intentional, and is COM_REUSE the applicable framework for the main corpus? | **no** |
| 5 | What exactly does "SIMAP's system metadata" cover — structured notice fields, or only system-level metadata? | **no** |

---

## 4. What the reply establishes, and what may not be inferred

**Establishes.**

1. The Commission's general re-use policy is governed by the Re-use Decision.
2. TED notices **and** metadata may be reused for **both commercial and
   non-commercial** purposes.
3. Reuse is conditioned on **source acknowledgement** and on the **copyright
   notice**.
4. Metadata are dedicated to the public domain under **CC0**.
5. Whether or not the EU asserts copyright over the database **should not prevent
   reuse** of TED data.
6. **The way the data are retrieved is not relevant in this regard.**

**Does NOT establish. None of these may be inferred, and each is refused by a
test.**

- ❌ that no database right exists
- ❌ that no sui generis database right exists
- ❌ that the EU waives all database rights
- ❌ that all TED fields are CC0
- ❌ that all TED content is CC0
- ❌ that reuse is unconditional
- ❌ that no attribution is required
- ❌ that redistribution is unlimited or unconditional
- ❌ any right to bypass technical controls, ignore rate limits, or bypass
  authentication

---

## 5. H-36A — reconciled by splitting a question that was two

The historical question asked whether the EU or the Publications Office asserts
database-level rights over the TED corpus, and recorded `NOT ESTABLISHED, in
either direction`. **The reply answers one half and explicitly declines the
other**, so the question is now carried as two.

| | old | reconciled |
|---|---|---|
| **A. Database-right existence / holder** | `NOT_ESTABLISHED` | **`NOT_ESTABLISHED`, and not necessary to resolve for the current reuse purpose** |
| **B. Is such a right a reuse blocker?** | not distinguished | **`OFFICIAL_FIRST_PARTY_GUIDANCE_INDICATES_NOT_A_BLOCKER`** |

**Existence did not move, and the reason is more specific than "the reply was
vague".** The words are *"whether or not the European Union asserts **copyright**
over the database"*. Directive 96/9/EC creates **two** distinct rights over a
database: copyright in the selection and arrangement (Article 3), and the sui
generis right of the maker (Article 7). The reply names the first. It does not
name the one the question named, and *"whether or not"* is a refusal to say
either way — recorded as a refusal rather than smoothed into an answer.

**Blocker status moved, and that is the substantive change.** The office that
would assert the right states in writing that it should not prevent citizens or
organisations from reusing the data, in answer to a request that described a
commercial SaaS in terms. The abstract legal ontology is unresolved and **does not
have to be resolved for this purpose**, because the rightholder-side body has said
it does not stand in the way.

**`NOT_ESTABLISHED` was not changed to `NO_RIGHT_EXISTS`, and never may be on this
evidence.**

---

## 6. H-36B — reconciled: retrieval-method neutrality for reuse

The historical issue was repeated extraction and re-utilisation, and whether the
route mattered. The operator asked about bulk downloads and the Search API by
name. The reply: *"The way in which the data are retrieved is not relevant in this
regard."*

Recorded as **`RETRIEVAL_METHOD_NEUTRALITY_FOR_REUSE`**, bounded twice:

- **It is not a database-right grant.** Article 7(3) of Directive 96/9/EC
  contemplates the right being granted by contractual licence. This is guidance,
  not a licence.
- **It is not `ANY_ACQUISITION_METHOD_IS_ALLOWED`.** Reuse rights and technical
  access rules are different questions. Nothing here authorises circumvention,
  anti-bot bypass, authentication bypass, rate-limit evasion, or an undocumented
  endpoint. **Governance continues to require an authorised technical route.**

### 6.1 The bulk route stays blocked, and its blocker changed identity

`ted-bulk-xml` was blocked by name because Mission 1.15.3 placed the highest
database-right exposure there. **The reply weakens exactly that reasoning.**

It stays blocked for an independent and now primary reason: **the bulk packages
offer no field selection.** `ted-personal-data-minimisation` requires minimisation
*at* acquisition, because an obligation about what is retrieved cannot be met by
discarding afterwards — and a bulk package delivers the whole notice including the
natural-person contact block. The Search API's `fields` parameter is what makes
the authorised route satisfiable.

**The route restriction is re-grounded, not relaxed.** Unblocking it would require
a minimisation story the route cannot currently tell.

---

## 7. Attribution — three regimes, and no universal rule

The reply conditions reuse on source acknowledgement. That maps onto **Article
6(2)(a)** of the Re-use Decision, which permits conditions including *"the
obligation for the reuser to acknowledge the source of the documents"* — verified
by re-reading the Decision in full (§9).

**This is stricter than the legal notice on its face**, and where two first-party
statements differ in strictness the stricter governs. The legal notice's own
sentence about procurement notices states no acknowledgement condition; the reply
does.

| material | instrument | obligation |
|---|---|---|
| **A. Procurement notice data** | Re-use Decision Art. 6(2)(a), as asserted by the publisher | **acknowledge the source**, per the copyright notice |
| **B. SIMAP editorial content** (TED, TED eNotices2, TED Developer Docs, TED Developer Portal) | CC BY 4.0 | **appropriate credit AND indication of changes** |
| **C. CC0 material** | CC0 1.0 | **none** |

**Implementation requirement: `TED_SOURCE_ATTRIBUTION_REQUIRED`.** The existing
`ted-attribution` condition already requires every product surface derived from
TED to carry the attribution the legal notice requires and to use no TED or SIMAP
logo, and it is verified by the `source-attribution-display` capability. **What
changed is its basis, not its existence**: attribution over the notices is now an
obligation under the Decision rather than an inference from a licence that covers
editorial content. Rendering work belongs to whichever mission builds a product
surface; nothing is rendered today.

---

## 8. Two residual questions the reply did not answer

### 8.1 CC0 scope — `UNRESOLVED`, and load-bearing

The operator asked precisely whether "SIMAP's system metadata" includes structured
fields inside procurement notices, or only metadata describing the SIMAP/TED
system itself.

- the reply says *"Metadata are dedicated to the public domain under CC-0"* and
  defines no boundary;
- the legal notice says *"The SIMAP system's metadata"* and defines none either.

**No structured TED notice field is classified CC0 by this review.** Reading the
reply's sentence as covering notice fields would answer question 5 in the
reuser's own favour with a sentence that was not addressed to it — and every
field this system retains would silently become public domain on that reading.

### 8.2 Catalogue licence mapping — `NOT_FULLY_RESOLVED`, and non-blocking

The reply confirms the general framework is the Re-use Decision. It does not
explain why some data.europa.eu distributions carry CC BY 4.0 while the main
`ted-1` distributions carry COM_REUSE, and does not state that COM_REUSE is
canonical for every main distribution.

**Why this is non-blocking:** reuse of the notices is authorised directly by the
legal notice and now by the publisher's written guidance, so the authorisation
does not depend on resolving the catalogue's licence metadata. **Legal
authorisation** and **catalogue metadata consistency** are separate questions.

Mission 1.15.3's condition stands: a licence is resolved from the resource's own
record and never carried across from another, so the twelve favourable CC BY files
still licence themselves and nothing else.

---

## 9. The legal notice and the Decision, re-inspected rather than quoted

**TED legal notice** (`https://ted.europa.eu/en/legal-notice`), retrieved
2026-09-04. Sections: Overview, Disclaimer, Copyright notice, Protection of your
personal data. The copyright notice reads, in relevant part:

> © European Union, 1998-2026 … Unless otherwise noted, procurement notices
> published in the Supplement to the Official Journal of the European Union can be
> freely reused for commercial or non-commercial purposes.

Third-party rights, industrial property and logos are excluded exactly as recorded
in earlier reviews. **Disclaimer:** the information is *"not necessarily
comprehensive, complete, accurate or up to date"* and is *"not professional or
legal advice"*; only electronically signed notices published in the Supplement are
authentic. **Retention:** notices are kept ten years on the TED website and are
then *"archived for historical purposes, in a non-public internal archive"*.

**Commission Decision 2011/833/EU**, re-retrieved 2026-09-04 in full from the
Publications Office's own Cellar repository. **The artifact is byte-for-byte the
one Mission 1.15.2 read: 4 pages, 16,748 characters.** The term scan was re-run
rather than quoted, and reproduces the earlier finding exactly:

```text
sui generis        0        database right     0        extraction         0
re-utilisation     0        Directive 96/9/EC  0        database           2
```

Both occurrences of *database* are the ones Mission 1.15.2 identified: an Article
2(2)(e) exclusion for unpublished research, and an example inside the Article 3(6)
definition of structured data. **Neither reaches the right H-36A asks about.**

Newly load-bearing: **Article 6(2)(a)**, the source-acknowledgement condition
(§7). Unchanged and carried forward: Article 3(2) defining reuse by *purpose*,
Article 6(2)(b) not to distort, Article 6(2)(c) non-liability, Article 2(4) no
reuse calculated to deceive or defraud.

---

## 10. Public retrievability is not preservation, and neither is a reliability

Two statements are recorded as **`POTENTIAL_FUTURE_RELIABILITY_BASIS`** and as
nothing else:

- the ten-year public window and the non-public internal archive after it;
- the accuracy, completeness and authenticity disclaimer.

Both could inform a future human reliability review of a TED measurement scope —
the first bears on `SOURCE_SIDE_CHECKABILITY` under
`human-reliability-assessment-rubric@1.0.0`. **This mission creates and alters no
ReliabilityAssessment.**

**Reuse rights and measurement dependability are different questions.** Reuse
asks *may this system use the data*; reliability asks *how dependably does this
measurement support this proposition*. A more permissive reuse position must
never raise a reliability, and an invariant test now enforces that the TED values
`0.5` and `0.55` are unchanged.

Long-term retrievability also does not withdraw reuse permission for data
lawfully obtained earlier. Those are separate facts and are kept separate.

---

## 11. Personal data — verified against the live deployment

The operator's request committed that natural-person contact information would not
be retained. **Measured rather than assumed**, against all TED records held:

| check | result |
|---|---|
| TED RawRecords | **188** |
| TED NormalizedRecords | **188** |
| distinct payload paths scanned (raw) | 97 |
| distinct payload paths scanned (normalized) | 34 |
| paths matching any of *contact, email, mail, phone, telephone, fax, address, person, family-name, given-name* | **0** |
| `organisations.buyer` / `organisations.tenderer` | **null on every record** |

The minimisation profile's `excluded` list — `contact_point`, `contact_name`,
`contact_email`, `contact_telephone`, `contact_fax`, `postal_address`,
`natural_person_name`, `personal_identifier` — covers every category the operator
named, and the collector in fact retrieved **less** than the profile authorises:
buyer and supplier organisation names are allowed and were never requested.

**No `TED_PERSONAL_DATA_MINIMISATION_GAP`.** Retention was not broadened, and no
research data was rewritten.

One observation, recorded because it is a reference and not a retention: each
record carries `links.*` and `source_reference.html` pointing at TED's own public
notice pages. Following one would retrieve the full notice including the contact
block. **Nothing does**, and the pointer is what makes the attribution obligation
in §7 satisfiable.

---

## 12. Decision table — `local-private-research-v1`, v2 → v3

**Verdict: `APPROVED_WITH_CONDITIONS` before and after.** The evidence
strengthened; the verdict had nowhere to go.

| condition | old state | new documentary evidence | new state | blocking? |
|---|---|---|---|---|
| `ted-attribution` | CAPABILITY, satisfied | reply: reuse *"provided that the source is acknowledged"*; Decision Art. 6(2)(a) | CAPABILITY, **re-verified satisfied**; **basis strengthened** (§7) | no |
| `ted-official-route-only` | CAPABILITY, satisfied | reply: retrieval method not relevant to reuse — and bulk still fails minimisation (§6.1) | CAPABILITY, **re-verified satisfied**; **basis re-grounded** | no |
| `ted-personal-data-minimisation` | CAPABILITY, satisfied | live scan, 0 personal-data fields in 188 records (§11) | CAPABILITY, **re-verified satisfied** | no |
| `ted-database-right-residual-exposure-accepted` | HUMAN_CONFIRMATION, satisfied 2026-09-01 | reply: database-copyright question should not prevent reuse | HUMAN_CONFIRMATION, **OUTSTANDING** | **YES** |

**The required-condition key set is unchanged between v2 and v3** — same four
keys, same four verification kinds — which is what makes the version bump honest
(`docs/CLAUDE.md` §Model inference execution). Asserted by a test, not assumed.

### 12.1 TED is INELIGIBLE under this profile until the operator acts

Appending v3 orphans the 2026-09-01 acceptance **by design**: verifications are
pinned to condition rows, and a new review version creates new ones. The three
capability conditions re-verified mechanically. The human one cannot.

```text
build_authorization('ted-eu', 'local-private-research-v1')  ->  REFUSED
  - review conditions not satisfied: ted-database-right-residual-exposure-accepted
```

**Mission 1.29's precedent was weighed, not ignored.** It withdrew an append
rather than orphan this exact condition — because there, recording an `UNCLEAR`
verdict that refused at the gate anyway gained nothing operational, so breaking
acquisition was pure loss. Here the record gains the load-bearing answer of the
whole TED arc and an attribution obligation the reply *imposes*, and **the thing
the operator accepted has itself changed**. A residual that is smaller is still a
residual, and the honest way to say *what you accepted is now different* is to ask
for the acceptance again.

**`record_ted_operator_acceptance.py` refuses, and its refusal is the authority
for this being a human act rather than a repoint:**

> REFUSED: this deployment carries review v3 and the acceptance was written about
> v2. … If the catalog really has moved on, the acceptance has to be made again by
> a person, not replayed.

That guard was written in Mission 1.15.6.1 and this is the first occasion it could
fire. **It was not repointed to v3**, because repointing it would turn a replay of
a decision already made into a record of one that has not been.

### 12.2 The statement to be accepted

Writing it down is not recording it (Mission 1.15.6). The acceptance a named
operator would be making is:

> I have read `ted-eu-official-reuse-response-v1.md`. I accept the residual
> database-right exposure for bounded queries through the authorised official
> routes under `local-private-research-v1`, review v3. I understand that what
> remains is smaller than what I accepted on 2026-09-01 and is not nothing: the
> Publications Office has stated in writing that the database-copyright question
> should not prevent reuse and that retrieval method is irrelevant to it, and it
> remains true that the existence and holder of a sui generis right are not
> established, that the reply is the publisher's guidance rather than an
> adjudication, and that the legal notice disclaims being legal advice.

No verifier may satisfy this, by design, and no command in this repository records
it.

---

## 13. Decision table — `commercial-multi-tenant-research-v1`, v5 → v6

**Verdict: `REQUIRES_REVIEW` before and after — and the blocker changed
identity.**

| activity / question | old state | new documentary evidence | new state | blocking? |
|---|---|---|---|---|
| `automated_access` | PERMITTED | retrieval method not relevant to reuse | PERMITTED | no |
| `api_use` | PERMITTED | — | PERMITTED | no |
| `commercial_use` | PERMITTED | **reply, answering a request describing a commercial SaaS by name** | PERMITTED, **first-party supported** | no |
| `storage` | PERMITTED | — | PERMITTED | no |
| `derived_analytics` | PERMITTED | reply covers commercial analytical use of notices and metadata | PERMITTED, **first-party supported** | no |
| `model_processing` | PERMITTED | Art. 3(2) purpose-framed (H-34, closed) | PERMITTED | no |
| `redistribution` | PERMITTED | legal notice *"can be freely reused"* — unchanged; reply is silent | PERMITTED **as to the grant**; carve-outs unresolved | see below |
| **H-36A / H-36B** | open, blocking | reply (§5, §6) | **materially addressed** | **no longer the blocker** |
| **raw redistribution / resale / customer-facing source access** | not separately tracked | **none — the request never described them** | **`NOT_ADDRESSED`** | **YES** |
| `external_model_egress` (profile-level) | `NOT_ASSESSED` | none | `NOT_ASSESSED` | **YES, independently** |

**Why it does not become eligible.** This profile declares `raw_redistribution`,
`raw_resale`, `customer_facing_source_access`, `public_access` and
`external_customers` all true. **The clarification request named none of them.**
It described retrieval, minimised storage, commercial *analytical* use, automated
processing and derived aggregate signals. A reply is an answer to the question
that was asked, so it cannot authorise acts the question never put.

And the carve-outs bite hardest exactly there: clearing additional rights where
content depicts identifiable private individuals or includes third-party works,
and Article 2(2)(b), are conditions a local analytical use satisfies by
minimisation and a customer-facing republication of notices cannot answer by the
same means.

**Commercial purpose is now first-party supported at the highest authority
available. Commercial purpose is not unrestricted redistribution.** Approving this
profile on a reply that answered a narrower question would be exactly the drift
`docs/CLAUDE.md` §Deployment model forbids.

---

## 14. Historical truth was preserved

Earlier missions correctly recorded that no authoritative Publications Office
reply was held. **That remains true of the time it was written**, and nothing was
rewritten to pretend otherwise.

```text
before 2026-09-04    no authoritative direct response held
on     2026-09-04    direct first-party response received
```

- `ted-eu-database-right-clarification-v1.md`, `ted-eu-database-right-review-v1.md`,
  `ted-eu-governing-decision-review-v1.md`, `ted-eu-h36-legal-review-packet-v1.md`
  and `ted-eu-database-right-clarification-request-v1.md` are **unchanged**.
- The request document still carries no `sent_at`, and the test asserting that
  still passes: **this document records that a reply was received; it does not
  retroactively make the repository the sender.**
- Review versions are **append-only**. Local v1 and v2, and commercial v1 through
  v5, are untouched.

## 15. The tripwire that was waiting for this

Mission 1.15.4 §32 refused a user-written transcription of a Publications Office
reply and installed assertions that **no source in the catalog carries an
`OPERATOR_CORRESPONDENCE` evidence row** — *"so the first one to appear should be a
deliberate act with a real document behind it, and this assertion is what makes it
deliberate."*

This is that first one. The tripwires fired, and they were re-pointed rather than
deleted: what they now assert is that the only `OPERATOR_CORRESPONDENCE` row in
the catalog is this one, that it carries a fingerprint, and that no other source
has acquired one.

**And it exposed a real model gap on the way.** `OPERATOR_CORRESPONDENCE` has been
a permitted `document_type` since migration 0004, and every evidence row was
required to carry an absolute `http(s)` URL — enforced in the schema, in
`PolicyEvidence.__post_init__` and in `validate_source_registry.py`. **A letter has
no URL**, so the enum permitted a class of evidence the URL rule refused, and the
refusal was invisible because nobody had tried. Migration 0033 is the narrowest
repair: correspondence and legal review may address themselves with a `mailto:`
locator and must then carry a `document_fingerprint`. **Both halves or neither.**
Every other evidence type still requires `http(s)`.

The rule's own justification did not reach the case it blocked — *"an assessment
that cannot be re-opened cannot be re-verified when the platform changes its
terms"* is an argument about **published pages**, which change under a stable
address. Correspondence is fixed when it is sent and is re-verified by producing
the message.
