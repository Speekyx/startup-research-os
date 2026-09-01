# Mission 1.17 — Local-Private Source Review Alignment

**Sprint 1. Authorized by the Mission 1.17 brief §1-§31.**

**Five `APPROVED_WITH_CONDITIONS` reviews under `local-private-research-v1`.
Four sources ELIGIBLE, one still BLOCKED.** ADR-027 is unchanged, no fallback was
added, and no research data was touched.

Full review: [`local-private-source-review-alignment-v1.md`](../data/local-private-source-review-alignment-v1.md).

---

## 1. The mismatch

### Why did the runtime refuse five previously approved sources? Was that refusal correct?

Because they had no review under the profile the runtime declares, and **yes, it
was correct.** ADR-027: *"Never transfer approval between profiles… Nothing falls
back."* Those five were reviewed for a public multi-tenant SaaS; nobody had
written down what they permit for this deployment, and the gate declined to guess.

The mismatch was **missing review work**, not a defect. ADR-027 arrived in Mission
1.15.5 after four of the five had already been reviewed and collected under a
model with no concept of a profile.

### Was ADR-027 changed? Was profile fallback added?

**No to both.** No inheritance, no "stricter profile", no "equivalent profile", no
fallback of any kind. The proof is in the result table: `ted-eu` is approving
locally and still **BLOCKED** commercially, and the five were blocked locally
until a review was written. Neither verdict reached the other.

### What is `local-private-research-v1` allowed to do? Does local mean non-commercial?

Read from the catalog rather than reconstructed: deployment `LOCAL`, single
operator, no public access, no external customers, **no raw redistribution or
resale**, no customer-facing source access, personal data `MINIMISED`. Derived
internal analysis **yes**, model inference **yes**, model training **no**,
embeddings **no**.

**Local does not mean non-commercial**, and the profile says so itself:
*"the research produced is used to discover, evaluate and launch commercial
products, so commercial-use rights must still be positively granted."* Every
review below treats `commercial_use` as a right the source must grant.

---

## 2. The reviews

### Which five, and which evidence was reused?

`world-bank`, `gdelt`, `eurostat`, `fred`, `openalex`. Each existing review's
first-party evidence was reused; **no decision was.** Every activity verdict was
reached by asking what the *local* profile does with the source, against the
source's own documents.

### Which new documents were required?

Three were **re-retrieved on 2026-09-01 and confirmed unchanged**:

- **World Bank** licensing — CC BY 4.0, *"any purpose, including commercial
  use"*, attribution and change indication, microdata excluded;
- **Eurostat** copyright notice — commercial re-use authorised under Decision
  2011/833/EU, with the non-EU/EFTA, Swiss/Austrian trade and third-party
  exclusions, and a modification-disclosure obligation;
- **GDELT** about page — *"unlimited and unrestricted use for any academic,
  commercial, or governmental use of any kind without fee"*, citation required.

Two **refused this environment**: FRED returned HTTP 403 and OpenAlex returned
403 or redirected to an index. Their recorded evidence is two and three days old
respectively, inside the framework's own 365-day interval, so it is relied on as
current — and both failures are recorded in the reviews rather than omitted.

### Verdict and conditions for each

| Source | Verdict | Conditions | Notable |
|---|---|---|---|
| `world-bank` | `APPROVED_WITH_CONDITIONS` | attribution-surface, dataset-licence-allowlist, microdata-excluded | `redistribution` recorded `PERMITTED_WITH_CONDITIONS` because the **licence** grants it, not because the profile does it |
| `gdelt` | `APPROVED_WITH_CONDITIONS` | gdelt-attribution | closed a gap `docs/CLAUDE.md` had named — see §3 |
| `eurostat` | `APPROVED_WITH_CONDITIONS` | attribution-surface, geographic-exclusion, trade-data-exclusion | the modification-disclosure obligation reaches derived analytics, not just republication |
| `fred` | `APPROVED_WITH_CONDITIONS` | fred-api-key, fred-endorsement-notice, copyrighted-series-excluded | evidence relied on without re-retrieval, recorded |
| `openalex` | `APPROVED_WITH_CONDITIONS` | openalex-contact-configured, openalex-spend-bounded | **the local profile is STRICTER here** — see §4 |

### What is deliberately *not* a condition

No redistribution, no resale, no customer-facing access, no model training, no
embeddings. Those are properties of the **profile**, carried by its definition and
by D-12. Writing them as source conditions would imply the source imposed them —
false for GDELT and World Bank, which both grant redistribution outright.

---

## 3. A gap the contract had named, now closed for this profile

GDELT's authorization context was handing collectors **all three routes**,
including `gdelt-doc-api`, which no review has ever assessed. Every GDELT review
since Mission 1.9.3 has been scoped to WEB-NGRAM, and `docs/CLAUDE.md` said so
outright: *"GDELT is the named gap… Restricting it is a review act."*

This mission is that act, for this profile. The local compliance entry declares a
`route_authorization` allowing `gdelt-web-ngram-files` and **blocking
`gdelt-doc-api` and `gdelt-bulk-files` by name**, so a blocked label has no
endpoint to read and nothing for the transport to be pointed at (ADR-028).

Verified: the local context now offers `DATASET_DOWNLOAD gdelt-web-ngram-files`
and nothing else. **The commercial context still carries all three**, unchanged —
closing it there is a commercial-profile review act this mission is not.

This mattered beyond tidiness: the review text said the DOC API was not
authorised while the context handed it over. A narrowing that exists only in the
review is not a narrowing, which is Mission 1.15.10's lesson arriving one layer up.

---

## 4. Where the local profile is stricter, not merely narrower

**OpenAlex.** It carries scholarly authorship — named people, affiliations,
identifiers. The local profile's personal-data posture is `MINIMISED`, so
`personal_data_handling` moved from `NOT_ADDRESSED` to
`PERMITTED_WITH_CONDITIONS` and `personal_data_risk` stays `IDENTIFIABLE`.

**It is the only one of the five where the local review imposes more than the
commercial one did**, and it is the answer to why a per-profile review is not a
formality: four of the five were narrower everywhere and one was not, and only
asking each question separately finds that out.

---

## 5. Authorization, after

| Source | local | commercial |
|---|---|---|
| `world-bank` | **ELIGIBLE** | ELIGIBLE, unchanged |
| `gdelt` | **ELIGIBLE**, WEB-NGRAM only | ELIGIBLE, unchanged, all three routes |
| `eurostat` | **ELIGIBLE**, no resource authorised | ELIGIBLE, unchanged |
| `fred` | **ELIGIBLE**, no resource authorised | ELIGIBLE, unchanged |
| `openalex` | **BLOCKED** — two conditions unsatisfied | BLOCKED, same two |
| `ted-eu` | ELIGIBLE, unchanged | **BLOCKED** — `REQUIRES_REVIEW`, unchanged |

**Did the commercial verdicts change? No.** Every commercial row above is
identical to before, and TED's commercial refusal is the isolation guarantee
working in the other direction.

**OpenAlex approving and still blocked is the honest outcome.** Approving and
eligible are different facts; this mission moved the first.

### Which resources are ready?

Source approval is not resource approval, and the result shows it: `world-bank`
3 datasets, `gdelt` 2 datasets, **`eurostat` and `fred` none** — their compliance
entries carry `datasets: null` and none was invented.

---

## 6. Data, and one correction

### Were historical RawRecords rewritten? Were any research APIs called?

**No to both.** No World Bank, GDELT, Eurostat, FRED or OpenAlex research call was
made. Policy-document retrieval only.

### Did any research-data counts change?

**None.**

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 23 / 23 | 23 / 23 |
| Signals / Claims / ClaimRevisions / Evidence | 8 / 8 / 8 / 8 | 8 / 8 / 8 / 8 |
| ReliabilityAssessments | 1 | 1 |
| Opportunities / Embeddings / Scores | 0 | 0 |

Catalog counts changed as expected: **62 reviews** (was 57), 96 evidence records,
40 review conditions, and four new local compliance entries.

### A correction to Mission 1.16

That report attributed the missing `use_profile` in provenance to the pre-ADR-027
collections. Measured here: **all 23 RawRecords lack it, TED's eleven included** —
the field is not written by any collector, including one built after ADR-027.

A separate and smaller gap: provenance records the review version and the rights
basis but not the profile the job declared. Recorded as backlog; it is not
governance alignment and fixing it here would have been scope creep.

---

## 7. Two defects this mission exposed

### A loader bug that only a second profile could reveal

`sros-source load` derived a condition's row id from `(source, review_version,
key)` with **no profile in it**. `world-bank` commercial v1 and `world-bank` local
v1 both declare `attribution-surface`, so both produced one id and the load raised
a primary-key violation.

The `ON CONFLICT` clause already named the right natural key —
`(review_id, condition_key)` — but the id is checked first. The review id itself
has carried the profile since Mission 1.15.5; the rows hanging off it never did,
and nothing had two reviews of one source sharing a condition key to notice.

Fixed generically, applying the rule the review id already uses, to both
conditions and evidence. **Not worked around by renaming conditions**: two reviews
of one source legitimately carry the same condition key — that is what it means
for two profiles to impose the same obligation.

### The Gateway defect got six times bigger, and reaches a second endpoint

`/api/v1/sources` duplicates a source once per profile that has reviewed it. While
`ted-eu` was the only source with two profile rows the blast radius was one;
aligning five more gave each a second row. **And `/api/v1/.../eligibility` has the
same profile-blindness**, now returning six conditions for `fred` where three
exist — the union over profiles, not over distinct conditions.

Both are asserted **as defects** so they fail the day they are fixed, and the
second endpoint is newly recorded: whoever fixes `/sources` would otherwise fix
half of it and still see green.

**Not fixed here**, per §31 and because choosing which profile the HTTP layer
answers for is a design decision with no default.

---

## 8. Tests

Existing tests failed for the right reason — the registry genuinely changed — and
each was repointed rather than weakened:

- three CLI tests used `world-bank` as their example of a source unreviewed under
  the local profile. Repointed at `reddit`, which genuinely is; the assertions are
  unchanged. The unreviewed count moved 28 → 23;
- the human-condition carrier count moved two → three, because OpenAlex now
  carries `openalex-spend-bounded` under each profile independently;
- GDELT's review-history test now scopes to the commercial profile, because
  version lines are per (source, profile) and an unscoped history interleaves two;
- the eligibility-view condition count is **scoped by profile on both sides** —
  the view always had one row per (source, profile) and the test's subquery
  counted every review of the source, which was the same number only while one
  profile had reviews.

Added: `test_the_five_aligned_sources_did_not_inherit_anything`, which asserts
each of the five has two **distinct** review objects, that the local one is
version 1 of its own line, and that it names `mission-1.17`. If a future change
ever satisfied the local profile by reading the commercial verdict, that is where
it shows.

### Did all gates pass?

**Yes.**

```text
zero-dependency suites            555 tests, 8 packages      exit 0
all pytest suites                 7 packages                 exit 0
seven validators                                             exit 0
contract generation --check                                  exit 0
all four generated-document checks                           exit 0
sros-source load / verify --apply                            exit 0
ruff check / ruff format --check                             exit 0
mypy                              144 source files           exit 0
environment-template secret check                            exit 0
assert_registry_grants_nothing                               exit 0
```

`sros-source render` regenerated the catalog document through its generator; no
generated file was hand-edited.

---

## 9. Is the project ready to resume source expansion?

**Yes — the blocker Mission 1.16 stopped on is gone.** The runtime profile and the
registry are coherent, four already-collected sources are eligible again, and a
new source's local review is now a normal review rather than a special case.

**Stack Exchange remains the first candidate**, for the reason 1.16 gave: a
question is solution-seeking by construction rather than by interpretation, and it
is the strongest fit in the registry for the `problem` family that TED covers only
nominally.

**What still blocks it is unchanged and is not something this mission could
touch:** its Public Network Terms of Service and Consolidated Responsible AI
policy are served behind an anti-bot interstitial, and neither `stackoverflow.com`
nor `api.stackexchange.com` is reachable from this environment. Retrieving them
from an environment that serves them is the whole of the next step; the review and
the implementation follow quickly once they exist, because every layer beneath is
now proven.

**If they cannot be retrieved**, the honest alternatives are Reddit — same
problem, `redditinc.com` equally unreachable — or accepting that the `problem` and
`desire` families stay uncovered until an environment that can read those terms is
available. Picking an easier source in a family already covered would enlarge the
corpus and change nothing about what the system can conclude.
