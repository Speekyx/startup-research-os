# Mission 1.8 — New Source Compliance Enablement, and a governance audit that cost more than it bought

**Date:** 2026-08-30
**Branch:** `sprint-1/mission-1.8`
**Status:** Complete. No collector implemented, no platform content collected.

**Deliverables:**
[`new-source-compliance-gap-analysis-v1.md`](../data/new-source-compliance-gap-analysis-v1.md) ·
[`gdelt-compliance-v1.md`](../data/gdelt-compliance-v1.md) ·
[`wikimedia-pageviews-compliance-v1.md`](../data/wikimedia-pageviews-compliance-v1.md)

---

## 1. PyPI governance consistency audit

**The question §2 asked: does the authoritative evidence positively grant the
assessed commercial multi-tenant SaaS use? No.**

PyPI's Mission 1.7 review cites one document, the Terms of Service effective
2025-02-25. Everything it establishes is a **prohibition**: abuse or excessively
frequent requests may suspend API access; tokens may not be shared to exceed
rate limits; the API may not be used to download data for spamming. There is no
grant of any kind.

So PyPI reached an approving state with **not one of the six activities the
assessed use materially requires positively permitted**. `commercial_use`,
`storage`, `derived_analytics` and `model_processing` were all `NOT_ADDRESSED`;
the only positive findings were "the API may be called" and "do not harvest
contact details".

### 1.1 The review diagnosed itself and was approved anyway

Its own committed `review_notes`:

> the approving state rests on the absence of a prohibition covering us plus the
> presence of a documented API, and commercial reuse itself is NOT_ADDRESSED

That is a description of the exact move Mission 1.7 §12 forbids — *do not infer
commercial permission from "API available" or "public content"* — written by the
reviewer who then recorded `APPROVED_WITH_CONDITIONS`.

**Being precise about a failure mode in prose is not the same as acting on it,
and the state is what the gate reads.** `source-registry-v1.md` §1 rule 2 has
said "uncertainty is never permission" since Mission 1.0. Nothing read it.

## 2. PyPI final verdict

**Outcome C. `REQUIRES_REVIEW`.** No new documentation was retrieved that
supplies the missing grant, and none was found. Review version 1 is preserved
unchanged: the useful history is that the reasoning was written down correctly
and acted on incorrectly.

### 2.1 The audit could not stop at PyPI

§4 forbids a one-off exception. Stating the rule that PyPI violated required
applying it to every approving source, and it caught two more.

| Source | auto | api | comm | storage | derived | model | Verdict |
|---|---|---|---|---|---|---|---|
| `world-bank`, `eurostat`, `fred`, `openalex`, `gdelt` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **holds** |
| `npm-registry` | ✓ | ✓ | ✓ | ✓ | ✓ | **—** | **downgraded** |
| `wikimedia-pageviews` | ✓ | ✓ | ✓ | **—** | ✓ | **—** | **downgraded** |
| `pypi` | ✓ | ✓ | **—** | **—** | **—** | **—** | **downgraded** |

**The line is not arbitrary.** Every source that holds has an explicit licence
or an explicit unlimited grant — CC-BY 4.0, the Eurostat copyright notice, the
FRED terms, CC0, GDELT's "any kind". Every source that fails rests on
terms-of-service silence.

**npm** had the same defect in milder form. Two assessments overstated their
evidence: "Commercial packages are welcomed expressly" is about what may be
*published to* npm, and the right to "copy, publish and analyze content" is
granted *to npm* — which version 1's own evidence note said in so many words
before the assessment recorded it as a permission of ours. Corrected, three of
six are unaddressed.

**Wikimedia** is §3 below.

Leaving either approving while downgrading PyPI would have been the one-off
exception §4 prohibits, pointed the other way.

## 3. Wikimedia Pageviews — exact condition inventory

Read from the catalog, not reconstructed.

| Key | Review | Verification | Obligation | State | Would need |
|---|---|---|---|---|---|
| `wikimedia-user-agent` | v1 | `HUMAN_CONFIRMATION` | every request carries a User-Agent naming client, version and contact | `UNKNOWN`, blocking | a generic request-identification capability — **does not exist** |
| `wikimedia-attribution` | v1 | `HUMAN_CONFIRMATION` | surfaces showing article **content**, not view counts, carry CC BY-SA attribution and a link | `UNKNOWN`, blocking | `source-attribution-display` — **exists** |

One profile: `PUBLIC_API` / `wikimedia-analytics-api`, no auth, no key,
**200 requests per minute** documented, `FREE_WITH_LIMITS`.

**Both conditions could have been made verifiable. The source is blocked for a
different reason**, and finding it is what stopped this mission achieving its
stated second objective.

### 3.1 The evidence that looked like a data licence is a documentation footer

Mission 1.7 cited the Analytics API documentation as labelling its content
CC BY-SA 4.0. That page carries `Content: CC BY-SA 4.0 · Code: MIT-0` — the
standard footer describing **the documentation site**, not the data the API
returns. Removing that misreading leaves `storage` and `model_processing` with
nothing behind them, and both are required.

### 3.2 The licence was retrieved and does not close it

CC BY-SA 4.0 was fetched during this mission and recorded as `OFFICIAL_LICENCE`
evidence. Section 2 grants *"reproduce and Share the Licensed Material"* and
*"produce, reproduce, and Share Adapted Material"*, commercially, with no
text-and-data-mining restriction. That is precisely the missing grant — **for
Licensed Material**.

Whether aggregate pageview *counts* are Licensed Material is **H-24**, an open
question the Mission 1.7 review itself recorded. Both answers are determinations
about what copyright subsists in, and `source-registry-v1.md` §0 states this
system is not a legal decision engine.

**Downgraded to `REQUIRES_REVIEW`**, H-24 promoted from a refinement to the
blocker, licence recorded so the next reviewer has both halves. §18 anticipated
this: *record exactly why; do not weaken the gate to achieve eligibility.*

## 4. GDELT — exact condition inventory

| Key | Review | Verification | Obligation | State |
|---|---|---|---|---|
| `gdelt-attribution` | v2 | `CAPABILITY` → `source-attribution-display` | cite the GDELT Project and link to it, on use and on redistribution | **SATISFIED** |

**One condition, because the review states one obligation.** Version 1 expressed
it as `HUMAN_CONFIRMATION` — not because it needs a person, but because no
compliance configuration existed and a capability with no parameters resolves
`UNKNOWN` for ever.

### 4.1 Two conditions considered and not written

§6 forbids inferring conditions that merely sound sensible, and both sounded
sensible.

- **An access restriction**, by analogy with World Bank's `indicators-api-only`.
  World Bank's exists because its review identified a carve-out — the Microdata
  Library — that had to be kept out of the request path. GDELT's review
  identifies none.
- **A dataset licence allowlist.** World Bank needs one because its platform
  distributes under several licences and the licence is a per-dataset property.
  **GDELT names no licence at all** — it grants unlimited use directly — so
  there is nothing to match and an allowlist would deny everything for a reason
  the terms do not give.

## 5. Compliance configuration architecture

Configuration, not code. No new capability was written and none was needed:
`source-attribution-display` describes itself as shared and parameterised, and
GDELT is the fourth source to use it.

## 6. Attribution

Two elements, both with wording the terms prescribe:

| Element | Text | Supplied? |
|---|---|---|
| `SOURCE_CREDIT` | `The GDELT Project` | no |
| `EXACT_NOTICE` | the citation-and-link sentence, verbatim | no |

No `MODIFICATION_STATEMENT`, no `DISCLAIMER`, no `LICENCE_IDENTIFIER` — the
terms require none and §8 forbids inventing wording. The absent licence
identifier is worth noting rather than blanking: GDELT grants unlimited use
directly rather than through a named instrument.

The validator caught that my first attempt lifted the notice from a
**paraphrase**. The verbatim sentence is now an `excerpt` on review version 2's
evidence, so a notice composed here rather than quoted would fail.

## 7. Access methods

Two reviewed profiles and no others: `PUBLIC_API`/`gdelt-doc-api` and
`DATASET_DOWNLOAD`/`gdelt-bulk-files`. No scraping, no browser automation, no
undocumented endpoint, no fallback host.

## 8. Resource scope

Not source-wide. Two rules, each traceable to something:

| Rule | Because |
|---|---|
| `third_party_denied: true` | the grant covers datasets GDELT **releases**; it aggregates worldwide news and holds no rights over the articles themselves |
| `require_dataset_family: true` | the review assessed two routes for a specific capability set; GDELT publishes more, and a resource that cannot say what it is has not been assessed |

Fail-closed in both directions: `THIRD_PARTY` refused, `UNKNOWN` refused,
unclassified refused, and a descriptor belonging to another source refused.

## 9. Identification and authentication

**None required, and none manufactured.** No key, no OAuth, no account — so no
`CONFIG_REFERENCE` condition, per §12. `runtime_credential_references` is empty.

Wikimedia's User-Agent requirement is the case §13 anticipated: an
**identification** obligation, not authentication. The right shape is a generic
`required-request-identification` capability, and it was **not built** — §7 and
§13 both forbid unused abstractions, and the compliance validator enforces it by
failing on "registered capabilities that no condition names". Wikimedia's
conditions live on a non-approving review, so the capability would have been
unused on the day it was written. Its specification is in
[`wikimedia-pageviews-compliance-v1.md`](../data/wikimedia-pageviews-compliance-v1.md) §3.2.

## 10. Rate limits

| Source | Documented | Recorded |
|---|---|---|
| `wikimedia-pageviews` | 200 requests / minute | `rate_limit_known=True`, `origin=DOCUMENTED` |
| `gdelt` (both profiles) | none published | `rate_limit_known=False`, every field null |

**Nothing invented.** GDELT publishes no limit, so pacing a future collector is
an engineering decision that must not be laundered through the registry — a
"reasonable default" recorded here would be read by a collector as the
provider's number.

## 11. Data minimisation

The validator rejected my first attempt, which had no profile at all, and it was
right: the omission was a real gap.

| | |
|---|---|
| **allowed** | event identifier, theme identifier, entity mention, tone score, period, geography, **content origin** |
| **excluded** | article full text, publisher content, personal data, user identifier |

`content_origin` is allowed for the reason FRED's `series_notes` is: the
third-party rule cannot be evaluated without it, so minimising it away would
remove the ability to honour the rule that makes the source usable.
`article_full_text` and `publisher_content` are the `third_party_denied`
boundary expressed at field level.

## 12. Condition verification

No boolean was flipped. `sros-source verify --apply` ran
`source-attribution-display` against the new configuration and recorded
`SATISFIED` with what it inspected. Twelve conditions across five approving
sources: **10 satisfied, 1 unsatisfied** (FRED's credential, absent in CI),
**1 unknown** (OpenAlex's spend ceiling, `HUMAN_CONFIRMATION`, still blocking).

## 13. Eligibility before and after

| | Before | After |
|---|---|---|
| Approving | 8 | **5** |
| Collector-eligible (environment) | 3 | **4** |
| Collector-eligible (catalog view) | 0 | 0 |
| `collector_enabled` | 1 | **1** |
| Collectors implemented | 1 | **1** |

Eligible: `world-bank`, `eurostat`, `fred`, **`gdelt`** — the first
non-economic source to reach the gate.

**Python and SQL agree on all 27 sources, zero divergences.** The expected
outcome is not hard-coded in the comparison; the point is that the two agree,
whatever they say.

## 14. Authorization contexts

Built for GDELT with no network request, from governance alone: source id,
review version 2, both approved access methods, baseline retention (30/365),
attribution elements, `third_party_denied`, rate-limit metadata recorded as
unknown, empty credential references, and a condition snapshot showing
`gdelt-attribution: SATISFIED`.

`build_authorization` raises for `wikimedia-pageviews`, `pypi` and
`npm-registry` — the gate refusing from the other side.

## 15. Registry mutation safety

```text
database unchanged by the run, across 20 tenant tables
global tables unchanged by the run, across 14 tables; 12 appended to 1 append-only table
```

Intended Mission 1.8 changes persisted; no test mutation did; no review was
rewritten; no condition silently toggled; `collector_enabled` unchanged. The
Mission 1.7 guard was not weakened.

## 16. Existing-data survival

Verified field by field, not by row count:

```text
six raw, six normalized — source_id world-bank only
values 67158348  67382061  67601110  82905782  83092962  83160871
identical to Mission 1.6.1 · no float artifact · all collector_version 1.1.0
every session link intact · six distinct content hashes · every quality VALID
```

## 17. Tests and CI

**873 tests across 6 packages.** New module `test_new_source_compliance.py`, 27
tests.

Three checks were corrected in ways worth recording, and each was **probed
against a deliberate violation** before being trusted:

| Check | What was wrong | Probe |
|---|---|---|
| `validate_source_registry` #12 (new) | nothing enforced §1 rule 2 | written against the **uncorrected** catalog; it named all three offending sources and their exact missing activities before any downgrade landed |
| `validate_compliance_capabilities` restriction tuple | `require_dataset_family` was not counted as a resource restriction — an omission that never showed because World Bank always set an exclusion list too | a scope with nothing set, `third_party_denied` off, and an empty minimisation list: all three still caught |
| my own new check, twice | it printed `ok` before knowing its own result | fixed both times before commit |

**The required-activity list exists in two places and a third test compares
them.** The validator runs with nothing installed (ADR-009) so it cannot import
the test module, and the test cannot import a script; two copies of one fact
drift, two copies plus a comparison do not.

One deliberate Mission 1.4 tripwire fired and was acknowledged rather than
derived away: `EXPECTED_ELIGIBLE` is written down *"so a change in either
direction fails"*, and GDELT joining it is exactly the acknowledgement it exists
to force.

## 18. New issues

- **`AttributionElement` has no per-record link value.** CC BY-SA attribution is
  satisfied by a hyperlink to the article, and the closed contract enum has no
  element for one. Two options, neither taken: add a value, or express the link
  as a `SOURCE_CREDIT` whose supplied text is a URL — a value in the wrong
  field. Recorded in the Wikimedia readiness document.
- **The developer family now rests on nothing.** npm and PyPI were its entire
  approving coverage and both are pending (**H-26**, **H-25**).
- **The materiality rule is a judgment about which activities are load-bearing.**
  Six are in the set and five are out, each for a stated reason. A future
  reviewer who disagrees about `redistribution` has a real argument to have, and
  the rule is written where they will find it rather than buried in a validator.

## 19. Remaining blockers

Unchanged: **D-03**, **D-08**, **D-10**, **D-12**, **PROFILE-NOT-CALIBRATED**,
**H-12**, **H-13**.
Changed: **H-22** half resolved, **H-24** promoted to a blocker.
New: **H-25** (PyPI), **H-26** (npm).

## 20. Mission 1.9 readiness

**Safe to begin.** One more source is eligible, the register is more honest,
Python and SQL agree everywhere, and the twelve World Bank records are
unchanged.

**Mission 1.9 should implement the GDELT collector.** It is eligible, free, needs
no credential, has a satisfied attribution condition and a fail-closed resource
scope, and it is the only non-economic source available. Its one open engineering
question is pacing, because GDELT publishes no rate limit — which is a decision
to make explicitly, not to record in the registry as though the provider had
stated it.

---

## The questions §31 asks explicitly

| Question | Answer |
|---|---|
| Was the PyPI Mission 1.7 approval consistent with "silence is not permission"? | **No.** Four of six required activities were `NOT_ADDRESSED` and the review's own notes named the defect |
| What is PyPI's current verdict? | **`REQUIRES_REVIEW`** (outcome C). Version 1 preserved |
| Were all Wikimedia conditions inventoried? | **Yes** — both, with verification kind, obligation, state and what would verify each |
| Were all GDELT conditions inventoried? | **Yes** — one, which is all its review states |
| Is Wikimedia Pageviews collector-eligible now? | **No** |
| Is GDELT collector-eligible now? | **Yes** — the fourth, and the first non-economic |
| If not, what exact conditions remain? | Wikimedia is not blocked on a condition at all. Its **review** is no longer approving: `storage` and `model_processing` have no grant, pending **H-24** |
| Do Python and SQL eligibility agree? | **Yes, across all 27, zero divergences** |
| Can `AcquisitionAuthorizationContext` be built for them? | **GDELT yes**, complete and with no network request. Wikimedia, PyPI and npm raise `AcquisitionNotAuthorizedError` |
| Are attribution obligations enforceable? | **GDELT yes**, by `source-attribution-display`, verified `SATISFIED`. Wikimedia's would be, once its review is approving |
| Are resource scopes fail-closed? | **Yes.** `THIRD_PARTY`, `UNKNOWN`, unclassified and cross-source descriptors are all refused, and both rules report rather than short-circuiting |
| Is Wikimedia's request-identification requirement represented? | **Specified, not built.** It needs a generic capability that no approving condition names, which the validator would reject as unused |
| Are official rate limits represented without invention? | **Yes.** Wikimedia 200/min `DOCUMENTED`; GDELT `UNKNOWN` on both profiles |
| Is `collector_enabled` still false for both? | **Yes.** Only `world-bank` is enabled, unchanged |
| Was any collector implemented? | **No.** `IMPLEMENTED_COLLECTORS == {"world-bank"}` |
| Was any platform research data collected? | **No.** Only CC BY-SA 4.0's legal code was retrieved, as policy evidence |
| Did the World Bank records survive unchanged? | **Yes**, verified field by field |
| Is Evidence Aggregation still uncalibrated? | **Yes.** Untouched |
| Is D-12 still open? | **Yes.** 0 signals, 0 vectors, 0 claims, 0 evidence rows |
| Which source should Mission 1.9 implement first? | **GDELT** |
| Is Mission 1.9 safe to begin? | **Yes** |

---

## What this mission actually cost

It set out to make two sources eligible and made one, by finding that the other
had been approved on a misreading. It also withdrew two approvals it was not
asked to look at.

The measurable result is worse than before: the economic share of approving
sources rose from 37% to **60%**, `entertainment` lost its only approving source,
and **eight of sixteen signal families now have none**.

That is the correct outcome and it should not be presented as a setback in
disguise. The coverage numbers Mission 1.7 reported were partly measuring
approvals that would not survive their own stated rule. **A coverage figure that
improves when the governance behind it gets stricter is measuring the wrong
thing**, and the useful comparison is not 8 approving against 5, but three
sources whose approval rested on evidence against three whose approval rested on
its absence.

---

## Validation

All 10 migrations applied to an empty database, with and without `--seed`, in a
scratch database so the six records were never at risk · RLS green ·
**873 pytest across 6 packages** · 337 zero-dependency · ruff check + format ·
mypy strict (113 files) · contract generation `--check` · `validate_schema` ·
`validate_source_registry` (**27 sources, 30 evidence records, 0 warnings**) ·
`validate_compliance_capabilities` (**12 conditions, 5 approving sources, 3
authorizable**) · `validate_evidence_aggregation` · `validate_normalization` ·
`assert_registry_grants_nothing` · `sros-source render --check` ·
`render_review_results.py --check` · `render_signal_coverage.py --check` ·
tsc (contracts + web) · eslint · `next build`

Post-suite: **20 tenant tables and 14 global tables unchanged**, 12 rows appended
to the append-only verification log.
