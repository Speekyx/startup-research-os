# Local-Private Source Review Alignment V1

**Authoritative.** Mission 1.17. Five sources reviewed against the profile the
runtime actually declares, reusing evidence and reusing no decision.

**Result: five `APPROVED_WITH_CONDITIONS` reviews; four sources ELIGIBLE, one
still BLOCKED.** ADR-027 is unchanged, no fallback was added, and no research
data was touched.

---

## 1. Why the mismatch existed

`SROS_USE_PROFILE=local-private-research-v1` and, before this mission, exactly
one review in the registry was under that profile. `world-bank`, `gdelt`,
`eurostat`, `fred` and `openalex` were approving under
`commercial-multi-tenant-research-v1` and refused at the gate.

**That refusal was correct.** ADR-027: *"Never transfer approval between
profiles… Nothing falls back."* Those five were reviewed for a public
multi-tenant SaaS. Nobody had written down what they permit for this deployment,
and the gate declined to guess.

The mismatch was not a bug in the gate. It was **missing review work**, created
by ADR-027 arriving in Mission 1.15.5 after four sources had already been
reviewed and collected under a model with no concept of a profile.

## 2. The rule this mission had to obey

> Evidence reuse is allowed. Decision reuse is not.

Every activity verdict below was reached by asking what the **local** profile
does with the source, against the source's own documents. The documents are the
same documents; the questions asked of them are different.

**Where the argument is short, it is short for a reason and the reason is
stated.** A licence that permits redistribution to customers for any purpose
cannot be read to forbid local storage without redistribution — that is applying
one piece of evidence to a narrower activity, not inheriting a verdict. Where the
local profile is *stricter* rather than merely narrower, it is called out
(OpenAlex, §3.5).

## 3. The five reviews

All are **version 1** of their own profile line, `reviewed_by mission-1.17`,
`APPROVED_WITH_CONDITIONS`, 365-day interval.

### 3.1 `world-bank`

**Evidence re-retrieved 2026-09-01 and unchanged.** CC BY 4.0: data may be
copied, modified and distributed *"in any format for any purpose, including
commercial use"*, with attribution and an indication of changes.

Every local activity is inside that grant. `commercial_use` is `PERMITTED` and
the deployment being local does not change it — the profile's own definition says
local is not non-commercial.

**`redistribution` is recorded `PERMITTED_WITH_CONDITIONS` because the licence
grants it**, not because the profile does it. The profile redistributes nothing;
that is our restriction, and recording it as `NOT_PERMITTED` would misattribute
our choice to the World Bank's licence.

Conditions carried forward unchanged: `attribution-surface`,
`dataset-licence-allowlist`, `microdata-excluded`. The exclusions are properties
of the catalogue, not of the use — a local deployment does not make a
non-CC-BY dataset CC BY.

### 3.2 `gdelt`

**Re-retrieved 2026-09-01 and unchanged.** *"All datasets released by the GDELT
Project are available for unlimited and unrestricted use for any academic,
commercial, or governmental use of any kind without fee."* Redistribution is
granted explicitly, subject to citation and a link.

The most permissive grant in the portfolio; no local activity needed an argument.
Condition: `gdelt-attribution`. `retention` stays `NOT_ADDRESSED` — GDELT states
no obligation, and `NOT_ADDRESSED` means the source is silent, never that any
retention is fine.

**This review closed a gap `docs/CLAUDE.md` had named.** Every GDELT review since
Mission 1.9.3 has been scoped to WEB-NGRAM, while the authorization context went
on handing a collector all three routes — including the DOC API that no review
has ever assessed. The contract said so in as many words: *"GDELT is the named
gap… Restricting it is a review act."*

This is that act, for this profile. The local compliance entry declares a
`route_authorization` allowing `gdelt-web-ngram-files` and **blocking
`gdelt-doc-api` and `gdelt-bulk-files` by name**, so a blocked label has no
endpoint to read and nothing for the transport to be pointed at (ADR-028). The
commercial context still carries all three; closing it there is a
commercial-profile review act this mission is not.

### 3.3 `eurostat`

**Re-retrieved 2026-09-01 and unchanged.** *"Reuse of statistical data, metadata,
publications, and other dissemination tools published on this website for
commercial or non-commercial purposes is authorised"*, under Commission Decision
2011/833/EU — the same instrument that governs TED, reaching us through a
different publisher.

`commercial_use` is `PERMITTED_WITH_CONDITIONS` and the conditions are the
publisher's: non-EU/EFTA country data, Swiss and Austrian trade data under
specific commodity classifications, and third-party copyrighted material are
excluded from free re-use.

**The modification-disclosure obligation is load-bearing for this system
specifically.** Eurostat requires changes to be disclosed and a disclaimer to
state that Eurostat bears no responsibility for alterations. Every layer above
normalization here is an alteration, so the obligation reaches derived analytics
rather than stopping at republication.

**No resource is authorised.** Eurostat has no collector and no selected dataset.
This approves capabilities; `resource_ready` stays NO.

### 3.4 `fred`

**Re-retrieval attempted 2026-09-01 and refused: HTTP 403 to this environment.**
The recorded evidence is from 2026-08-29 — three days old, well inside the
framework's own 365-day interval — so it is relied on as current, and the failed
attempt is recorded rather than hidden.

Conditions: `fred-api-key` (the terms require a key), `fred-endorsement-notice`
(a specific disclaimer so derived work is not read as the Federal Reserve Bank of
St. Louis endorsing it), `copyrighted-series-excluded`.

**No resource is authorised.** No collector exists.

### 3.5 `openalex` — the one place the local profile is stricter

**Re-retrieval attempted 2026-09-01 and refused:** `openalex.org` returned 403
and the documentation host redirected to an index. Same treatment as FRED, for
the same reason.

**`personal_data_handling` moved from `NOT_ADDRESSED` to
`PERMITTED_WITH_CONDITIONS`, and `personal_data_risk` stays `IDENTIFIABLE`.**
OpenAlex carries scholarly authorship: named people, affiliations, identifiers.
The local profile's posture is `MINIMISED`, so a future collector acquires the
minimum its evidence semantics need and author identity is not assumed to be part
of that. **This is the only one of the five where the local profile imposes more
than the commercial review did**, and it is the reason a per-profile review is not
a formality.

`api_use` is `PERMITTED_WITH_CONDITIONS`: OpenAlex asks for a contact address to
reach its polite pool, which is a courtesy owed rather than a restriction on the
data.

## 4. What is NOT encoded as a source condition, and why

No redistribution, no resale, no customer-facing source access, no model
training, no embeddings.

Those are properties of the **profile**, carried by its own definition and by
D-12 for embeddings. Writing them as source conditions would imply the source
imposed them, which for GDELT and World Bank would be false — both grant
redistribution explicitly.

## 5. Historical data is not retrospectively authorised

RawRecords collected before ADR-027 existed carry no `use_profile` in their
provenance. They are left exactly as they are: not rewritten, not deleted, not
recollected, and no historical profile is invented for them. They were authorised
under the governance model in force when they were collected, and this review is
**prospective only**.

**A correction to Mission 1.16 while measuring it.** That report attributed the
missing `use_profile` to the pre-ADR-027 collections. In fact **all 23 RawRecords
lack it, TED's eleven included** — the field is simply not written by any
collector, including one built after ADR-027. That is a separate, smaller gap:
provenance records the review version and the rights basis but not the profile
the job declared. Recorded as backlog; fixing it is not governance alignment.

## 6. Authorization, after

| Source | `local-private-research-v1` | `commercial-multi-tenant-research-v1` |
|---|---|---|
| `world-bank` | **ELIGIBLE** | ELIGIBLE, unchanged |
| `gdelt` | **ELIGIBLE**, WEB-NGRAM route only | ELIGIBLE, unchanged, all three routes |
| `eurostat` | **ELIGIBLE**, no resource authorised | ELIGIBLE, unchanged |
| `fred` | **ELIGIBLE**, no resource authorised | ELIGIBLE, unchanged |
| `openalex` | **BLOCKED** — `openalex-contact-configured`, `openalex-spend-bounded` unsatisfied | BLOCKED, same two |
| `ted-eu` | ELIGIBLE, unchanged | **BLOCKED** — `REQUIRES_REVIEW`, unchanged |

**The last row is the isolation guarantee working in both directions.** TED is
approving locally and refused commercially; the five are approving under both and
were refused locally until somebody did the work. Neither verdict reached the
other.

**OpenAlex approving and still blocked is the honest outcome**, not a failure.
Approving and eligible are different facts: this mission moved the first, and the
second waits on a contact address and a person confirming a spend ceiling.

## 7. Resource-level truth

Source approval is not resource approval, and the difference is visible in the
result:

- `world-bank` — 3 datasets authorised (Indicators API), unchanged;
- `gdelt` — 2 datasets authorised (WEB-NGRAM), unchanged;
- `eurostat`, `fred` — **no dataset authorised**, and none invented. Their
  compliance entries carry `datasets: null`, which is what makes the review
  capability-level rather than a wildcard.

## 8. Open questions

1. Re-retrieve the FRED API Terms of Use and the OpenAlex API documentation from
   an environment that serves them, and confirm the recorded evidence.
2. The DOC API and bulk routes remain unreviewed for GDELT under **both**
   profiles; the commercial context still carries them.
3. No Eurostat or FRED resource has been operationally selected.
4. OpenAlex's two conditions are unsatisfied on this deployment.
5. `use_profile` is absent from every RawRecord's provenance, on every source.
