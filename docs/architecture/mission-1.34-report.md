# Mission 1.34 — Multi-Scope Opportunity Evidence Architecture V1

**Outcome:** `MULTI_SCOPE_ARCHITECTURE_READY_SCOPE_RELATIONS_UNPOPULATED` (§34 B)

**Branch:** `sprint-1/mission-1.34`
**Design artifact:** [`opportunity-multiscope-sufficiency-design-v1.md`](../data/opportunity-multiscope-sufficiency-design-v1.md)
**Demonstration:** [`scope-architecture-demonstration-v1.json`](../data/scope-architecture-demonstration-v1.json)

---

## 0. Outcome, and why it is B rather than A

The architecture works. It represents direct and broader-scope contextual
Evidence, keeps their scopes apart, and fails closed without an explicit
relation — which is §34 A's test, and the demonstration passes it on real data.

**It is B because no cross-scope relation can legitimately be populated from
existing canonical data, and none was invented.** The relation registry ships
empty. Mission 1.33 refused to assert which commercial category contains Docker;
§33 forbids inventing one here; so the capability exists and holds zero edges.
§34 names B as valid and potentially expected, and reporting A would mean
counting a capability as an achievement it has not yet had the chance to be.

The consequence is worth stating plainly: **no Evidence row in this deployment
can currently be contextual, because contextual requires an edge and there are
none.** Every one of the 28 rows is either direct evidence for its own subject or
refused.

---

## 1. §0 — where `Evidence subject == Opportunity subject` was assumed

Found by reading, not by assuming. Seven places, and the first is the load-bearing
one:

1. **`packet.build_packet`** — `dimensions = frozenset().union(*(f.dimensions for
   f in facets))`. **The union has no scope term.** Membership in a packet WAS
   the claim of aboutness, so any row in a packet contributed its dimensions to
   that packet's subject unconditionally.
2. **`grouping.group_by_subject`** — one bucket per subject token. A row is in a
   packet only if it shares the subject, so there was exactly one membership
   class and no second one to be.
3. **`grouping.CandidateGroup`** — `key`, `facets`, `canonical_subject_id`. No
   per-row role.
4. **`facets.EvidenceFacets`** — twelve facts side by side, `dimensions` and
   `dimension_bound` among them, and no scope.
5. **`sufficiency.evaluate`** — reads `packet.counting_dimensions`, which came
   from that union. So any row's dimensions could satisfy the diversity rule.
6. **`subjects.CanonicalSubject`** — `subject_id`, `display_name`,
   `description`, `identifiers`. No level.
7. **`hypothesis.OpportunityHypothesis`** — `supported_dimensions` and
   `unsupported_dimensions` as bare `frozenset[EvidenceDimension]`. Exactly the
   flattening §8 forbids: a `MARKET_ACTIVITY` of a category and a
   `PROBLEM_OR_NEED` of the product are the same shape in the same set.

Two things were already right and were left alone: `MarketScope` answers WHERE
and is untouched, and the dimension definitions already ask about *the bounded
scope observed* — the vocabulary anticipated this mission, and the packet model
had nowhere to put the answer.

---

## 2. The thirty-three answers

### 1. What new scope vocabulary exists?

`SubjectScopeType` — `PRODUCT | CATEGORY | MARKET | GEOGRAPHY`, procedure
`observation-scope@1.0.0`. Exactly the four §1 requires; no fifth was added.
Each carries a `means`, a non-empty `never_means`, and an
`example_in_this_repository` — and `MARKET`'s example says **"none"**, because no
registered source observes one and nothing was invented so the vocabulary would
look complete.

### 2. How is PRODUCT represented?

*One bounded, separately identifiable thing that somebody built and publishes
under a name.* Defined by what it IS, not by being narrower than CATEGORY — §1
forbids the positional definition, and a test asserts the word "narrower" does
not appear in it. Its `never_means` starts with the organisation that publishes
it, because the canonical registry already says `docker` is the platform and not
the company.

### 3. How is CATEGORY represented?

*A published classification whose members are several distinct things*, whose
identity comes from the classification that defines it and not from any member.
Its `never_means` includes *a market* — a classification is how a publisher files
things, and a market is where they are exchanged.

### 4. How is MARKET represented?

*A bounded space of economic activity — buyers, sellers and exchange — broader
than one classification, identified by the activity rather than by a filing
rule.* Its `never_means` names the trap directly: CPV division 72 is a CATEGORY
however wide it is.

### 5. How is GEOGRAPHY kept separate?

Two ways. **As a `SubjectScopeType`** it means the observation's SUBJECT is a
place — a World Bank series is about Germany. **`MarketScope` is untouched** and
still answers where an Opportunity applies. `GEOGRAPHY`'s `never_means` names
`MarketScope` explicitly as the other question, and a test asserts that
`GLOBAL`, `REGION`, `COUNTRY` and `MULTI_COUNTRY` are not members of the new
vocabulary.

Orthogonality is also structural: `ObservationScope.geography` is a separate
optional field, so a CATEGORY observed in France carries both, and an absent
geography means UNASKED rather than GLOBAL.

### 6. How is ObservationScope represented?

A frozen record carrying scope type, a stable `scope_id`, a display name, a
status, an origin, the source-native identifiers it was established from, a
basis, the procedure version, and an optional geography. Constructor rules:
`RESOLVED` requires a type, an origin and a basis; `UNDETERMINED` refuses all
three, so a level cannot sit beside a status saying nobody established one.

**Nothing is persisted.** The scope is derived at packet-build time from the
Signal's own scope and the reviewed registries, by the same `subject_key`
procedure grouping already uses — so there is no migration, no column, no
historical backfill, and no second answer to drift from the first.

### 7. How is an Opportunity subject represented?

Unchanged: `subject:docker` in `CanonicalSubject`, same three subjects, same six
identifiers. The registry moved to `canonical-subject-registry@1.1.0` and gained
one required field per subject, `scope_type`, with a stated basis. The
Opportunity's scope comes from that entry and **never from its evidence** —
inferring it from the packet is how a packet full of category rows would quietly
become a category Opportunity.

### 8. How are scope relations represented?

`ScopeRelation`, in `scope-relation-registry@1.0.0`. Three typed containments —
`SUBJECT_WITHIN_CATEGORY`, `CATEGORY_WITHIN_MARKET`, `SCOPE_WITHIN_GEOGRAPHY` —
whose endpoint types are **enforced at construction**, not documented. Matching
is exact scope-id equality on both endpoints.

**No transitive expansion** (§4): product-in-category plus category-in-market
does not yield product-in-market, and a test asserts the third lookup returns
`None` while the first two return edges. A reflexive edge is refused, and a
`WITHDRAWN` edge licenses nothing.

### 9. What provenance is required for a relation?

Narrower and broader scope id and type, relation type, origin, basis,
`reviewed_by`, `reviewed_at`, status. A blank basis is refused; a
`HUMAN_REVIEWED` relation with nobody named is refused.

Origins are `SOURCE_NATIVE`, `HUMAN_REVIEWED`, `DETERMINISTIC_REGISTRY`. **There
is no `MODEL_INFERRED`**, in the enum or anywhere in the mission (§5).

### 10. What is DIRECT evidence?

`DIRECT_SUBJECT_EVIDENCE`: the row's observation scope IS the Opportunity's
subject scope, by exact equality. It needs no relation — there is nothing to
relate — and `ScopedEvidence` refuses a direct row that carries one, because
recording an admitting containment would suggest the subject is inside something.

### 11. What is CONTEXTUAL evidence?

Two roles, kept apart. `BROADER_SCOPE_CONTEXT`: the row observes a broader scope
that an ACTIVE reviewed relation says contains the subject.
`GEOGRAPHIC_CONTEXT`: the row observes a place. They are separate members rather
than one flag because a country is not a bigger version of a product, and merging
them would let a macroeconomic series read as category context.

A contextual row with no admitting relation is refused at construction, so a row
that cannot name the edge that let it in did not come through the gate.

### 12. Can contextual Evidence satisfy direct Evidence requirements?

**No, structurally.** `ScopedOpportunityEvidencePacket.direct_dimensions` is
built only from rows whose role is direct, and there is **no property on the
class that unions direct and contextual dimensions** — a test enumerates every
public attribute and asserts a contextual `MARKET_ACTIVITY` appears in none of
them.

That is a structural no rather than a policy no. A policy no is relaxed by
editing a threshold; this one has to be built, on purpose, by somebody.

### 13. Can CATEGORY `MARKET_ACTIVITY` become PRODUCT `MARKET_ACTIVITY`?

No. It stays `context(CATEGORY:X).MARKET_ACTIVITY`. There is no inheritance, no
promotion, no lower-confidence variant, and no parameter that would enable one
(§25). The packet's `limitations()` says so in words, and `statement()` puts the
scope in the sentence's SUBJECT rather than in a trailing qualifier, because a
qualifier is what a summariser drops.

### 14. Can CATEGORY `ECONOMIC_VALUE` become PRODUCT `ECONOMIC_VALUE`?

No, same mechanism, own test.

### 15. Can CATEGORY buyer existence become PRODUCT buyer existence?

No, same mechanism, own test.

### 16. Does contextual evidence establish WTP?

**No** (§18). No role, no scope and no relation produces
`WILLINGNESS_TO_PAY`: dimensions are carried verbatim and there is no mapping
table that converts one into another at any scope. Tested over
`ECONOMIC_VALUE`, `BUYER_OR_BUDGET_EXISTENCE` and `MARKET_ACTIVITY` as inputs.
The taxonomy's own three near-misses — a listed price, a budget line, a public
contract total — are re-asserted here so Mission 1.33's finding cannot erode
quietly.

### 17. Were existing Docker Evidence rows scoped?

Yes, and verified rather than assumed (§20). All **8** resolve to
`PRODUCT / subject:docker`, origin `HUMAN_REVIEWED`, because the canonical
registry maps both their source-native keys and declares that subject `PRODUCT`.
Nothing else about them changed: no Claim, no Signal, no dimension, no
reliability, no independence.

### 18. Was TED Evidence scoped?

Yes: **`CATEGORY / ted-eu:CPV-division:90`**, origin `SOURCE_NATIVE`. The basis
is the publisher's own: a CPV division is a division of the Common Procurement
Vocabulary, which is a classification by its own name and construction. This
repository still does not know what division 90 covers, and the rule does not
require it to.

### 19. Was any TED Evidence attached to Docker?

**No.** Offered to the Docker Opportunity, it was refused
`NO_PERMITTED_RELATION`. That refusal is the demonstration §32 C asks for.

### 20. Was any Docker→category relation invented?

**No** (§29, §33). `scope-relation-registry-v1.json` holds `"relations": []`, and
records under `explicitly_not_recorded` both the edge that was not written
(`subject:docker → ted-eu:CPV-division:90`) and why. A test asserts the registry
is empty and that it names the CPV case.

The canonical registry likewise gained no parent: a test asserts the words
`parent`, `broader`, `within` and `contains` appear in no key of it.

### 21. Did Docker's existing packet remain formable?

**Yes, and this was verified by re-running the real preparation.** The artifact
was regenerated after every change in this mission and diffed structurally
against the committed one:

> **exactly one field differed across the whole document** — the recorded
> `subject_registry` version, `1.0.0 → 1.1.0`.

Every packet id, every dimension set, every eligibility count, every sufficiency
verdict and every external-synthesis availability was identical. The Docker
packet is still 8 rows, `HYPOTHESIS_FORMABLE`, counting dimensions
`AUDIENCE_OR_USAGE` and `PROBLEM_OR_NEED`.

The scoped packet's direct half reproduces it: 8 direct rows, same two counting
dimensions, asserted by a test that reads both artifacts.

### 22. Did Opportunity revision 1 change?

**No.** One Opportunity, one revision, still revision 1 with its 12 unsupported
dimensions. No revision 2 was created (§11, §21).

### 23. Did its seven evidence links change?

**No.** Still 7.

### 24. Were any canonical research records created?

**No.** All thirteen counters verified against the live database and unchanged —
see §3 below.

### 25. Were any network calls made?

**No.** The demonstration reads the local database and writes one JSON file; the
engine modules import no HTTP client, asserted over the AST.

### 26. Were any model calls made?

**No.** 0.00 USD. No Gateway import, no provider SDK, no
`sros_semantic_equivalence` import anywhere in the five new modules, asserted
over the AST.

### 27. Did scoring/ranking occur?

**No.** `scoring.scores` still does not exist, D-03 is untouched, and every
Docker row is still `NON_SCORABLE` with `MISSING_RELIABILITY`.

### 28. Is reliability unchanged?

**Yes** (§23). One `ReliabilityAssessment`, the same one, for the TED scope. None
was created. A row can be contextually relevant and `NON_SCORABLE` at once, and
scope work touched neither property.

### 29. Is independence unchanged?

**Yes** (§24). Still `UNKNOWN` on every row, still 0
`EvidenceIndependenceGroups`. A scope relation establishes containment and says
nothing about independence; nothing in the new code reads or writes an
independence state.

### 30. Is Problem-Family still PARKED?

**Yes.** `PARK_PROBLEM_FAMILY_CLASSIFIER` stands, production inference remains
`NOT_AUTHORISED`, and a test asserts that any mention of `SAME_PROBLEM_FAMILY` in
the new modules occurs beside the word PARKED.

### 31. What migrations/schema changes occurred?

**None. No migration was needed and none was written.** The ledger is still at
`0031`.

That was a decision with a reason, not an omission. The scope is DERIVED at
packet-build time from identifiers already held; persisting it would freeze a
derivation in a column, which is what `source-registry-v1.md` §3 refuses for
eligibility and for the same reason. The registries are reviewed JSON documents,
exactly like `canonical-subject-registry-v1.json` has been since Mission 1.30.

So: no new tenant table, no RLS change, no tenancy question to answer, and no
historical Evidence row to backfill. §12's option A — deterministic derivation —
is what the corpus supports, and where it does not the answer is `UNDETERMINED`
rather than a manufactured level.

### 32. Test results?

**65 new tests**, all passing; **329 in the opportunity-engine package**; all CI
gates green — see §4.

Three Mission 1.30 tests were repaired, none weakened: two constructed a
`CanonicalSubject` before the level existed and now pass it, and one asserted the
recorded registry version, which legitimately moved to 1.1.0.

**One design defect the tests found**, and it is worth recording: my first gate
applied §15's dimension clause to DIRECT rows, which refused Mission 1.32's
deliberately dimensionless Docker row and made the scoped packet 7 rows against
the legacy packet's 8. §15 states its conditions for broader-scope inclusion; a
direct row is not being included on the strength of anything. The clause is now
contextual-only, the direct half reproduces the legacy packet exactly, and a test
pins both halves of the distinction.

**One clause was removed rather than written**: §15's *provenance is preserved*
is already enforced by `EvidenceFacets` (dimensions require a bound) and
`ObservationScope` (a resolved scope requires a basis). A duplicate check in the
gate could never fire, and an unreachable guard reads as protection while
protecting nothing. The test asserts both upstream constructors instead.

### 33. Recommended next mission?

**Mission 1.35 — Docker Commercial Scope Mapping V1**, exactly as §36 shapes it.

Determine, from an authoritative source-native taxonomy, which CATEGORY contains
`PRODUCT subject:docker` — without treating the two as identical. Its output is
one reviewed `ScopeRelation` with a stated basis, or the finding that no
published taxonomy supports one. The registry, the loader, the endpoint typing
and the gate are all built and waiting; what is missing is the edge, and an edge
is a reading of a document rather than a piece of code.

**Only after such an edge exists** may a later mission use TED's category
Evidence as context, and even then it enters as `BROADER_SCOPE_CONTEXT` at CPV
scope and contributes to no direct dimension.

If no useful hierarchy can be represented safely, the fallback stays Reliability
/ Scoring Eligibility Foundation.

---

## 3. Canonical counters (§31)

Verified against the live database after every change.

| Counter | Expected | Actual |
|---|---:|---:|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / Evidence | 28 each | **28 each** |
| ClaimRevisions | 29 | **29** |
| EvidenceIndependenceGroups | 0 | **0** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / revisions / links | 1 / 1 / 7 | **1 / 1 / 7** |
| Embeddings / Scores | 0 / 0 | **0 / 0** (`scoring.scores` absent) |
| Registered sources | 29 | **29** |
| Latest migration | 0031 | **0031** |

**Scope tables gained no rows because there are no scope tables.** The registries
are documents, and their contents are: 3 subjects each declaring `PRODUCT`,
2 source-native scope rules, **0 relations**.

Scope resolution over the corpus: **25 of 28 rows resolved, 3 UNDETERMINED** (the
GDELT lexical terms — a word names no level of thing, and they already map to no
dimension). Nothing was mass-labelled to make the corpus tidy.

---

## 4. CI-equivalent verification

| Gate | Result |
|---|---|
| `generate.py --check` | ok |
| `run_python_tests.py` | all suites passed |
| `validate_schema.py` | 9 invariant groups, 43 tables |
| `migrate.py --plan` | well formed, ledger at 0031 |
| `validate_source_registry.py` | 29 sources, 0 warnings |
| `validate_compliance_capabilities.py` | 34 conditions, 13 approving pairs |
| `validate_normalization.py` / `validate_signals.py` / `validate_claims.py` | 9 / 7 / 11 boundary groups |
| `validate_evidence_aggregation.py` | 8 checks, scoring still blocked |
| `ruff check` / `ruff format --check` | clean, 587 files |
| `mypy` (13 packages) | no issues |
| generated-doc `--check` steps (4) | all match |
| `run_pytest_suites.py` | passed across 9 packages; database unchanged |
