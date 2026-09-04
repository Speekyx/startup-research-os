# Mission 1.45 — TED Official Re-use Response Governance Reconciliation V1

**Primary outcome: `TED_OFFICIAL_REUSE_GUIDANCE_RECONCILED`** (§ Mission outcomes A).

The Publications Office answered the clarification request this repository has
carried as an unsent draft since Mission 1.15.3. **H-36A and H-36B are reconciled,
neither is overclaimed, and the load-bearing residual is a question the reply did
not answer rather than one it answered badly.**

**And the mission ends at an operator gate that it created deliberately.**
Appending a review version orphans the human acceptance recorded on 2026-09-01,
so **TED is ineligible under `local-private-research-v1` until a named operator
records it again.** No TED acquisition is planned, so the cost is bounded; the
reason is that what the operator accepted has itself changed.

```text
reviews appended     local v2 -> v3      commercial v5 -> v6
research data requests   0               governance document requests   6 (4 URLs)
model calls              0               reliability assessments changed  0
migration                0033            personal-data fields found       0 of 188
```

Artifacts:
[the reconciliation](../data/ted-eu-official-reuse-response-v1.md)
· `source-catalog-v1.json` (append-only)
· `0033_correspondence_evidence_locator.sql`.

---

## Final report

### The document

**1. Exact first-party email sender?** **Jose Antonio DOMÍNGUEZ ROJAS**,
`Jose-Antonio.DOMINGUEZ-ROJAS@publications.europa.eu`.

**2. Exact role?** **Head of Sector — Copyright and legal issues.**

**3. Organisation?** **Publications Office of the European Union**, Direction D —
Corporate Services, D.2 Contracts and Copyright.

**4. Date?** **2026-09-04, 11:17.**

**5. Subject / case identifier?** *"Clarification request regarding database
rights and reuse of TED procurement data"*, case **`2026-COP-201`**.

The artifact is a 3-page PDF export, 172,677 bytes,
`sha256:faee1e541c88bbd254f0660d2ebdb89e70766eb532a2192174e856ec5f922f74`.
**It is not committed.** It carries a named official's direct telephone number and
email and the operator's personal address, and this repository is public —
committing it would publish exactly the category of data this mission verifies the
TED pipeline does not retain. The fingerprint, the operative text and the
re-opening mailbox are preserved instead.

### The question that was asked

**6. Was the full original operator request inspected?** **Yes** — pages 2 and 3
of the artifact, quoted in full in the reconciliation document. Not summarised
from the brief.

**7. Did it explicitly describe commercial SaaS use?** **Yes**, verbatim:
*"Startup Research OS, a commercial software-as-a-service application"*. **This is
load-bearing**: a permission obtained by describing a smaller product is a
permission for a product we are not building, and this request did not describe a
smaller product.

**8. Repeated collection?** **Yes** — *"repeated collection"*.
**9. Bulk downloads?** **Yes**, by name.
**10. Search API?** **Yes**, by name.
**11. Automated processing?** **Yes** — *"automated processing, extraction and
classification"*.
**12. Derived analytics?** **Yes** — *"generation of aggregate market intelligence
and derived analytical signals"*.
**13. No current model training?** **Yes** — *"We are not currently intending to
use TED data for model training."*

### What the reply says

**14. Exact first-party statement on commercial reuse?**

> Under this framework, TED notices and metadata may be reused for both commercial
> and non-commercial purposes …

**15. Non-commercial reuse?** The same sentence, which grants both together.

**16. Attribution?** *"provided that the source is acknowledged"*.

**17. Copyright notice condition?** *"and according to the copyright notice
(link)"*. **The hyperlink resolves to `https://ted.europa.eu/en/legal-notice`** —
extracted from the PDF's own link annotations rather than assumed, which is what
anchors the condition to a specific instrument.

**18. Exact statement on database copyright / reuse?**

> Whether or not the European Union asserts copyright over the database should not
> prevent citizens or organisations from reusing the TED data.

**19. Exact statement on retrieval method?**

> The way in which the data are retrieved is not relevant in this regard.

### What may not be inferred

**20. Does the email say no database right exists?** **No.** It says *"whether or
not"*, which is a refusal to say — and it says **copyright** over the database,
while Directive 96/9/EC creates two distinct rights: copyright in the selection
and arrangement (Article 3) and the sui generis right of the maker (Article 7).
**It does not name the right the question named.**

**21. Does it waive every database right?** **No.** It waives nothing. A waiver
would be an act; this is guidance about what should not prevent reuse.

**22. Does it explicitly authorise circumvention?** **No.** Nothing in it
addresses technical access at all.

**23. Does it define all structured notice fields as CC0?** **No**, and this is
the most consequential non-answer — see 40.

### The legal notice, re-inspected

**24. Exact finding on procurement notices?**

> Unless otherwise noted, procurement notices published in the Supplement to the
> Official Journal of the European Union can be freely reused for commercial or
> non-commercial purposes.

**25. Exact finding on editorial content?** The editorial content of the SIMAP
websites — TED, TED eNotices2, TED Developer Docs, TED Developer Portal — is
licensed **CC BY 4.0**. **A different subject from the notices**, and conflating
the two is the error the evidence row exists to prevent.

**26. Exact CC BY condition?** *"provided appropriate credit is given and changes
are indicated"*.

**27. Exact finding on SIMAP metadata / CC0?** *"The SIMAP system's metadata is
dedicated to the public domain in accordance with the Creative Commons Universal
Public Domain Dedication deed (CC0 1.0)."* **The notice does not say what that
phrase covers.**

**28. Third-party rights?** *"You may need to clear additional rights if content
depicts identifiable private individuals or includes third-party works. To use
content not owned by the EU, you may need permission directly from
rightholders."*

**29. Logo / trademark restrictions?** Industrial property — *"patents,
trademarks, registered designs, logos and names"* — is excluded from the reuse
policy and not licensed; the SIMAP logos including TED's may not be used without
prior consent.

**30. Was the Re-use Decision inspected?** **Yes, re-retrieved in full** from the
Publications Office's own Cellar repository — EUR-Lex returned an empty body
again, as in Missions 1.15.1 through 1.15.3. **The artifact is byte-for-byte the
one Mission 1.15.2 read: 4 pages, 16,748 characters**, and the term scan was
re-run rather than quoted:

```text
sui generis 0   database right 0   extraction 0   re-utilisation 0   96/9 0
database 2  ->  Art. 2(2)(e) research exclusion; Art. 3(6) structured-data example
```

Newly load-bearing: **Article 6(2)(a)**, *"the obligation for the reuser to
acknowledge the source of the documents"* — which is exactly the condition the
reply asserts, now applied to the notice corpus itself.

### H-36, reconciled

**31. H-36A old state?** *"whether a sui generis database right SUBSISTS in the
TED notice corpus is NOT ESTABLISHED, in either direction."*

**32. H-36A reconciled state?** **Split, because the reply answers one half and
declines the other.**

| | state |
|---|---|
| database-right **existence / holder** | **`NOT_ESTABLISHED`**, and not necessary to resolve for this purpose |
| whether such a right **blocks reuse** | **`OFFICIAL_FIRST_PARTY_GUIDANCE_INDICATES_NOT_A_BLOCKER`** |

**`NOT_ESTABLISHED` was not changed to `NO_RIGHT_EXISTS`**, and on this evidence
never may be. A test asserts it.

**33. H-36B old state?** *"whether the applicable right holder GRANTS or WAIVES
the extraction and re-utilisation the engine needs is NOT ADDRESSED for either
route."*

**34. H-36B reconciled state?** **`RETRIEVAL_METHOD_NEUTRALITY_FOR_REUSE`**,
established by a statement directly responsive to the question that named both
routes.

**35. Is retrieval-method neutrality established?** **Yes, for reuse** — and it is
not a database-right grant. Article 7(3) of Directive 96/9/EC contemplates a
contractual licence; this is guidance, not a licence.

**36. Does this authorise only legitimate technical routes?** **Yes, and nothing
changed there.** Reuse rights and technical access rules are different questions.
No circumvention, anti-bot bypass, authentication bypass, rate-limit evasion or
undocumented endpoint is authorised, and governance still requires an authorised
route.

**The bulk route stays blocked and its blocker changed identity.** It was blocked
because Mission 1.15.3 placed the highest database-right exposure there, and the
reply weakens that reasoning. It remains blocked because **the bulk packages offer
no field selection**, so minimisation cannot happen *at* acquisition — and a bulk
package delivers the whole notice including the contact block. **Re-grounded, not
relaxed.**

### Scope of what is now supported

**37. Is commercial analytical use now first-party supported?** **Yes**, at the
highest authority available: the office that publishes TED, answering a request
that described a commercial SaaS by name.

**38. Is unrestricted redistribution supported?** **No.** The reply is silent on
redistribution, resale and customer-facing exposure, and the request described
none of them. **Commercial purpose is not unrestricted redistribution.**

**39. Is COM_REUSE vs CC BY catalogue mapping fully resolved?** **No —
`DATASET_DISTRIBUTION_LICENCE_MAPPING: NOT_FULLY_RESOLVED`.** Question 4 received
no direct answer. **It is non-blocking**, because reuse of the notices is
authorised by the legal notice and the reply directly, so authorisation does not
depend on the catalogue's licence metadata. Legal authorisation and catalogue
metadata consistency are separate questions.

**40. Is the exact scope of "SIMAP system metadata" fully resolved?** **No, and it
is the load-bearing residual.** Question 5 asked precisely whether it covers
structured notice fields. The reply says *"Metadata are dedicated to the public
domain under CC-0"* and defines no boundary; the legal notice defines none either.
**No structured TED notice field is classified CC0 by this review.** Reading the
reply's sentence as covering notice fields would answer the question in the
reuser's own favour with a sentence not addressed to it.

### The two profiles

**41. Local-private profile before?** `APPROVED_WITH_CONDITIONS`, v2, four
conditions, all satisfied, **eligible**.

**42. Local-private profile after?** `APPROVED_WITH_CONDITIONS`, **v3**. The
evidence strengthened and the verdict had nowhere to go.

**43. Remaining local conditions?**

| condition | new state | blocking? |
|---|---|---|
| `ted-attribution` | re-verified `SATISFIED`; **basis strengthened** to Art. 6(2)(a) | no |
| `ted-official-route-only` | re-verified `SATISFIED`; **basis re-grounded** on minimisation | no |
| `ted-personal-data-minimisation` | re-verified `SATISFIED` | no |
| `ted-database-right-residual-exposure-accepted` | **OUTSTANDING** | **YES** |

**The required-condition key set is unchanged between v2 and v3** — same four
keys, same four verification kinds — which is what makes the bump honest. Asserted
by a test rather than assumed, and the compliance configuration was re-pinned from
review v2 to v3, which is the re-check a version bump owes.

**44. Commercial-multi-tenant profile before?** `REQUIRES_REVIEW`, v5, with all
six load-bearing activities `PERMITTED` and H-36A/H-36B as the blocker.

**45. Commercial-multi-tenant profile after?** `REQUIRES_REVIEW`, **v6**.

**46. Remaining commercial conditions — and the blocker changed identity.** What
held this profile was H-36, and the reply materially addresses it. **What now
blocks it is the part of the profile the operator's own question did not
describe.** The profile declares `raw_redistribution`, `raw_resale`,
`customer_facing_source_access`, `public_access` and `external_customers` all
true; the request named none of them. A reply is an answer to the question that
was asked. And the carve-outs bite hardest exactly there — clearing rights where
content depicts identifiable private individuals, and Article 2(2)(b), are
conditions a local analytical use satisfies by minimisation and a customer-facing
republication cannot answer by the same means. Independently,
`external_model_egress` is `NOT_ASSESSED` for this profile.

**Approving it on a reply that answered a narrower question would be exactly the
drift `docs/CLAUDE.md` §Deployment model forbids.**

### Attribution and personal data

**47. Attribution implementation requirement?** **`TED_SOURCE_ATTRIBUTION_REQUIRED`.**
Three regimes, kept apart, with no universal rule invented: the **notices** carry
an acknowledgement obligation under Art. 6(2)(a) as asserted by the publisher;
**SIMAP editorial content** carries CC BY 4.0 credit plus indication of changes;
**CC0 material** carries none. The existing `ted-attribution` condition already
requires it on every product surface and is capability-verified — **what changed
is its basis, not its existence.** Rendering belongs to whichever mission builds a
product surface; nothing is rendered today.

**48. Personal-data minimisation status?** **Verified against the live deployment
and consistent with the operator's stated commitment.** The `excluded` list covers
every category the request named.

**49. Did the current TED collector retain any disallowed natural-person fields?**
**No.** Measured, not assumed:

| check | result |
|---|---|
| TED RawRecords / NormalizedRecords | **188 / 188** |
| distinct payload paths scanned | 97 raw, 34 normalized |
| paths matching *contact, email, phone, telephone, fax, address, person, family-name, given-name* | **0** |
| `organisations.buyer` / `organisations.tenderer` | **null on every record** |

The collector in fact retrieved **less** than authorised: buyer and supplier
organisation names are permitted and were never requested. **No
`TED_PERSONAL_DATA_MINIMISATION_GAP`**, and retention was not broadened.

### What was deliberately not moved

**50. Training permission changed?** **No.** Not assessed, not authorised, on
either profile.
**51. Embeddings permission changed?** **No.** Unassessed and blocked
independently by D-12.
**52. External model egress changed?** **No.** `NOT_ASSESSED` on the commercial
profile and `PERMITTED_TO_APPROVED_PROVIDERS` on the local one, exactly as before.
**Ordinary reuse is not egress to a third-party model processor**, and the reply
says nothing about one. H-39 is untouched.

**53. Were historical reviews rewritten?** **No.** Local v1–v2 and commercial
v1–v5 are byte-identical; the catalog diff is **255 insertions and 0 deletions**.
Every earlier document — `ted-eu-database-right-clarification-v1.md`,
`ted-eu-database-right-review-v1.md`, `ted-eu-governing-decision-review-v1.md`,
`ted-eu-h36-legal-review-packet-v1.md` — is unchanged, and the unsent request still
records that nothing was sent. **The reply arriving does not retroactively make
this repository the sender.**

**54. Was a new append-only review/version created?** **Yes**, two: local **v3**
and commercial **v6**, each the maximum of its own contiguous line.

**55. Exact documentary provenance stored?** Three new evidence rows per review,
kept separate because they establish different facts: the reply as
`OPERATOR_CORRESPONDENCE` with its case id, sender role, office, date, excerpt and
fingerprint; the legal notice re-inspected as `OFFICIAL_TERMS`; the Decision
re-retrieved and re-scanned as `OFFICIAL_LICENCE`.

**56. Research data acquired?** **`RESEARCH_DATA_REQUESTS = 0`.** No TED Search
API call, no notice downloaded, no bulk package, no pilot, no re-run.

**57. Governance documents fetched?** **`GOVERNANCE_DOCUMENT_REQUESTS = 6` across
4 distinct URLs** — the TED legal notice (×3, one URL), the Publications Office
publication record, EUR-Lex (returned an empty body), and the Cellar download
handler.

**58. Any ReliabilityAssessment changed?** **No. Zero.**
**59. TED 0.5 unchanged?** **Yes.**
**60. TED 0.55 unchanged?** **Yes.**

**A more permissive reuse position must never raise a reliability**, and an
invariant test now enforces it. Reuse asks *may this system use the data*;
reliability asks *how dependably does this measurement support this proposition*.
Two statements from the legal notice — the ten-year public window before a
non-public internal archive, and the accuracy/authenticity disclaimer — are
recorded as **`POTENTIAL_FUTURE_RELIABILITY_BASIS`** and as nothing else.

**61. Evidence counters changed?** **No.** RawRecords 325, NormalizedRecords 325,
Signals 33, Claims 43, ClaimRevisions 44, Evidence 57 — all unchanged.
**62. Opportunity counters changed?** **No.** 1 / 1 / 7.
**63. Scores?** **None.** `scoring.scores` does not exist.
**64. Model calls?** **Zero. 0.00 USD.** No embeddings.
**65. Problem-Family status?** **Still PARKED.**

### 66. Exact unresolved governance questions

1. **Database-right existence and holder** — `NOT_ESTABLISHED`, and not necessary
   to resolve for the current purpose.
2. **CC0 scope of "SIMAP's system metadata"** — `UNRESOLVED`, and load-bearing.
   The only residual that would change what this system may treat as public
   domain.
3. **COM_REUSE vs CC BY catalogue mapping** — `NOT_FULLY_RESOLVED`, non-blocking.
4. **Raw redistribution, resale and customer-facing source access** —
   `NOT_ADDRESSED`; the blocker for the commercial profile.
5. **`external_model_egress` under the commercial profile** — `NOT_ASSESSED`,
   independent of everything above.
6. **Rate limits** — still unpublished for the Search API, the SPARQL endpoint and
   the bulk packages; carried forward unchanged.

### 67. Recommended next mission

**Not a TED acquisition.** The reply improves permission and changes no
mathematics.

**First, the operator gate**: a named operator records the acceptance for review
v3, and TED becomes eligible again under `local-private-research-v1`. The
statement to be accepted is written out in §12.2 of the reconciliation document.
**Writing it down is not recording it**, and no command in this repository records
it — `record_ted_operator_acceptance.py` replays a decision already made, refuses
against v3, and **was deliberately not repointed**, because repointing it would
turn a replay into a record of a decision nobody has taken.

**Then the strategic roadmap, unchanged: Mission 1.46 — Independent Statistical
Evidence Route Feasibility V1**, over Eurostat or FRED beside World Bank. Mission
1.43's finding is arithmetic and this governance answer does not touch it: without
a second provenance group or a contradiction, the full aggregator is
algebraically indistinguishable from reliability pass-through.

---

## The model gap the first correspondence found

**`OPERATOR_CORRESPONDENCE` has been a permitted `document_type` since migration
0004, and no row had ever carried one.** Mission 1.15.4 §32 installed tripwires
asserting exactly that — *"so the first one to appear should be a deliberate act
with a real document behind it, and this assertion is what makes it deliberate."*

This is that first one, and **it could not be stored.** Every evidence row was
required to carry an absolute `http(s)` URL, enforced in three places: the schema
CHECK, `PolicyEvidence.__post_init__`, and `validate_source_registry.py`. **A
letter has no URL.** The enum permitted a class of evidence the URL rule refused,
and the refusal was invisible because nobody had tried.

**The rule's own justification does not reach the case it blocked.** It states the
reason: *"an assessment that cannot be re-opened cannot be re-verified when the
platform changes its terms"*. That is an argument about **published pages**, which
change under a stable address. Correspondence is fixed when it is sent, cannot be
silently amended, and is re-verified by producing the message.

**Migration 0033 is the narrowest repair.** Correspondence and legal review may
address themselves with a `mailto:` locator — for TED,
`op-copyright@publications.europa.eu`, the mailbox the legal notice itself
publishes and the address the request was sent to — and must then carry a
`document_fingerprint`. **Both halves or neither**: a mailbox with no fingerprint
names a channel rather than a document, and a fingerprint with no locator names
bytes nobody can ask about. Every other evidence type still requires `http(s)`,
and a fingerprint is still *not* required of published pages, because demanding
one would force a re-fetch to prove a row still valid.

## Repairs, and one pattern that recurred inside this mission's own tests

**Forty-four tests failed on the append**, and every one was repaired by keeping
the property and dropping the incidental number:

- **Version lines pinned to their length** — `legacy == [1, 2, 3, 4, 5]` and
  `local == [1, 2]`. Now: each line starts at 1, is contiguous, has no duplicates,
  and the two advance independently. `testing-strategy.md` §68.
- **Fixtures hard-coding `review_version=2`** — now read the current version from
  the catalog through one shared helper, so the next legitimate append does not
  look like a broken test.
- **Tests reading "the current review" to check what an earlier mission
  recorded** — pinned to the version that mission wrote. A test that follows
  `current` to assert what Mission 1.15.1 said is a test asserting that no later
  mission may ever answer an open question.
- **The two `OPERATOR_CORRESPONDENCE` tripwires** — re-pointed, not deleted. They
  now assert that the only such rows are the ones recorded here, that they carry a
  fingerprint, that none predates 2026-09-04, and that no other source has
  acquired one.
- **`test_only_the_current_review_version_is_satisfied`** — its own docstring read
  *"v1 owns its own row and stays FALSE. **A future v3 would too.**"* Mission
  1.15.6.1 predicted this exact moment; the assertion now states the invariant it
  was describing.

**And three of the five failures in this mission's own new test file were the
`testing-strategy.md` §23 shape** — a scan for a forbidden phrase failing on the
sentence that forbids it. In a file whose entire subject is not overclaiming, the
assertions that no overclaim appears kept tripping over the passages listing what
may not be claimed. Sixth, seventh and eighth occurrence of that shape; the fix is
the same each time, which is to scan the assertions and not the rules.

## What this mission did not establish

- **Not a legal guarantee, and not legal advice.** The reply is the publisher's
  stated reuse policy. The legal notice disclaims being legal advice in its own
  words.
- **Not that no database right exists**, and not that any right was waived.
- **Not that all TED data is CC0**, and no structured notice field was moved into
  it.
- **Not unrestricted redistribution**, and not customer-facing exposure.
- **Not a reliability.** No assessment was created, changed, superseded or
  re-based, and the reply was not attached to one.
- **Not eligibility.** TED is ineligible under the local profile right now, and
  the operator is the only one who can change that.
