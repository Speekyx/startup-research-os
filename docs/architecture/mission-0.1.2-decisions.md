# Mission 0.1.2 — Decision Resolution Register

Version: 1.0
Status: Authoritative index of resolutions
Date: 2026-08-27
Authority: explicit human decisions recorded in the Mission 0.1.2 brief
Predecessor: [`mission-0.1.1-decisions.md`](mission-0.1.1-decisions.md)

This register continues the Mission 0.1.1 register rather than editing it. The
0.1.1 file records what was true at the end of that mission and is not rewritten;
its §5 points here for the items that have since moved.

Before implementing anything, read both registers. Together they say what is
settled and which document governs it.

---

## 1. Resolution table

| ID | Original issue | Decision | Status | Governing document |
|----|----------------|----------|--------|--------------------|
| **D-01** | `ResearchContext` was referenced by the scoring framework but modeled nowhere. Blocked the `research-orchestrator` input contract | **`ResearchContext` is an input specification / value object**, not a persisted entity. It carries market scope, market and product types, domains, audience, languages, budget and technical constraints, desired MVP complexity, research depth, time horizon and exclusions. Stored as an **immutable snapshot** on a `ResearchSession` for reproducibility | **RESOLVED** | [Ontology V2](../domain/opportunity-ontology-v2.md) §11.3 |
| **A-06** | Same as D-01, from the audit's ambiguity list | Resolved by the same definition. `ResearchContext` now has a shape, a lifetime and an explicit reason for not being an entity | **RESOLVED** | Ontology V2 §11.3 |
| **A-11** | "research run", "Research Session" and `ResearchContext` were three names for adjacent concepts, with no defined relationship | **`ResearchSession` is the canonical persisted execution entity.** `ResearchProject` is the persistent workspace-scoped grouping. `ResearchContext` is the input snapshot. **`research run` is retired**; no `ResearchRun` entity is introduced. Code uses `ResearchSession` / `research_session_id` | **RESOLVED** | Ontology V2 §11, §11.5 |
| **A-05** | Geographic scope granularity undefined — a score's primary key and cross-row comparability depended on it | **`MarketScope`**, a closed discriminated union on `type`: `GLOBAL \| REGION \| COUNTRY \| MULTI_COUNTRY`. Countries are ISO 3166-1 alpha-2; regions come from a controlled registry. `COUNTRY` carries exactly one country, `MULTI_COUNTRY` two or more; lists are canonicalized | **RESOLVED** (geographic axis) | Ontology V2 §4 |
| **A-07** | Which §3 taxonomies are closed enums and which are open registries | **Closed enums** where code branches exhaustively: `ClaimType`, `MarketScope.type`, demand signal family, `EvidenceLevel`, `ResearchSessionStatus`. **Extensible registries** for evolving taxonomies: Market Type, Product Type, User Motivation, User Behavior, Value Proposition, demand signal type, Retention Mechanism, Monetization Model, Distribution Channel, Risk, Region. V1/V1.1/V2 values become **initial registry entries**, not database enums | **RESOLVED** | Ontology V2 §14 |
| **A-08** | `MONEY` (motivation) appeared to duplicate `MONEY_MAKING` (value proposition) | **Not duplicates. Neither removed.** `MONEY` answers *why the user acts*; `MONEY_MAKING` answers *what the product provides*. They are independent axes that frequently co-occur but neither implies the other | **RESOLVED** | Ontology V2 §13 |

Every row ends `RESOLVED`. No decision in the Mission 0.1.2 brief was left
unapplied.

---

## 2. Consequential changes

| Change | Reason |
|--------|--------|
| `docs/domain/opportunity-ontology-v2.md` created; V1.1 marked superseded and retained | The six resolutions are domain semantics and belong in the ontology |
| V2 preserves V1.1 numbering for §1–§10 | Every existing `§N ≤ 10` reference stays valid. New material is §11–§16 |
| `PROJECT_MANIFEST.md` → v1.2 | Authoritative ontology is V2; lifecycle names and taxonomy-governance principle added |
| `docs/CLAUDE.md` → v1.2 | Boot sequence → V2; canonical invariants gain research lifecycle, market scope and taxonomy governance |
| Gateway API renamed: `/v1/research-runs` → `/v1/research-sessions`, plus `/v1/research-projects` | A-11: endpoints are the most visible place a retired term would survive |
| `run_id` → `research_session_id` in current documentation | Same. The mapping for accepted ADRs is stated in Ontology V2 §11.5 |
| `ResearchSessionStatus` canonicalized to UPPERCASE | Closed enums are UPPERCASE (V2 §14.2). The states themselves are unchanged from Mission 0.1 |
| `packages/contracts/README.md` rewritten | `UserMotivation` moved from closed enum to registry reference; identifiers, `MarketScope` validators and `ResearchContext` added |
| Testing strategy gains domain-shape assertions | Scope invariants, snapshot immutability, status semantics and rediscovery are cheap to test and expensive to fix after a schema freeze |
| Quality gates gain `MarketScope` validators and a registry-vs-enum lint | A taxonomy declared as a database enum silently undoes A-07 |

---

## 3. Deliberately NOT resolved

| ID | Item | Why it stays open |
|----|------|-------------------|
| **D-03 / A-02 / A-03 / A-04** | Evidence aggregation formula, recency decay, independence thresholds, contradiction penalties | **Explicitly forbidden by the Mission 0.1.2 brief §13.** Still the project's hardest blocker: `services/scoring` cannot be implemented (`scoring-framework-v1.1.md` §13) |
| **A-12** | *New in this mission.* Non-geographic (audience/segment) scoping and how it composes with `MarketScope` | See §4 |
| — | Opportunity identity resolution — deciding two discoveries are the same opportunity | An analytical problem, not a schema problem. Ontology V2 §12.3 forbids solving it implicitly with a convenient unique constraint |
| **A-01** | Sparse vs dense scoring-profile weight vectors | Not in this mission's scope |
| **D-07** | Source registry and legal review records | Blocks `acquisition` |
| **D-08** | Score recomputation policy | Interacts with V2 §12: an opportunity now accumulates evidence across sessions, which sharpens the question |
| **D-11** | Observability stack | Conventions fixed regardless |
| **D-12** | Embedding re-embedding strategy | — |
| — | Region registry contents | Data Engineering |
| — | GDPR/jurisdiction analysis | Requires human or legal input |

---

## 4. New finding opened in Mission 0.1.2

### A-12 — Non-geographic scope is unspecified

**Where:** `opportunity-ontology-v1.md` and `v1.1.md` §4 listed market analysis as
"global, regional, country-level, or **segment-level**". The authorized
`MarketScope` (V2 §4.1) has four types, none of which is segment.

**Problem:** audience or segment scoping (for example "indie game developers",
"K-12 teachers") has no representation. Either it was dropped deliberately, or it
belongs on a separate axis that nothing currently defines.

**How it was handled:** V2 §4.8 records `MarketScope` as covering the
**geographic axis only**, and states explicitly that segment scoping is a
different axis deliberately not folded into it. Folding an audience dimension
into a geographic discriminated union would make both harder to query and
impossible to combine — a `COUNTRY_AND_SEGMENT` variant is the shape that
decision would eventually force.

**Severity:** ambiguity, not contradiction. It blocks nothing in Mission 0.2
provided schema design treats scope as geographic. It becomes expensive only if
segment-level scores are later required and `MarketScope` has to absorb them
after rows exist.

**Not resolved here**, and it must not be resolved by an implementer choosing a
shape.

---

## 5. How to use this register

1. **Before implementing:** check §1 here, then §1 of the 0.1.1 register. If the
   concern appears, the governing document is authoritative — follow it, do not
   re-derive it.
2. **If it appears in §3 of either register:** stop. Do not choose a value.
   Record the blockage and raise it (`docs/CLAUDE.md` §Change control).
3. **If it appears in neither:** it may be genuinely new. Add it to
   `specification-audit.md` with an id rather than resolving it in code.
