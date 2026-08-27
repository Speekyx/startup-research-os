# Mission 0.1.1 — Decision Resolution Register

Version: 1.0
Status: Authoritative index of resolutions
Date: 2026-08-27
Authority: explicit human decisions recorded in the Mission 0.1.1 brief

This is the lookup table. Before implementing anything, check here first: it tells
you what is settled and which document now governs it. What is *not* settled is
in `specification-audit.md` §6 and in §3 below.

---

## 1. Resolution table

| ID | Original issue | Decision | Status | Governing document |
|----|----------------|----------|--------|--------------------|
| **C-01 / D-02** | BullMQ is Node-only; the backend, workers and ML stack are Python. A Python worker cannot consume a BullMQ queue | **Remove BullMQ from the stack.** Celery + Redis for all asynchronous work. All-Python backend. No Node worker tier. TypeScript confined to `apps/web` and `packages/*` | **RESOLVED** | [ADR-004](adr/ADR-004-celery-redis-job-architecture.md); `PROJECT_MANIFEST.md` v1.1 §Technology Stack |
| **D-05** | Single-user tool or multi-tenant SaaS? Unanswered, and unanswerable cheaply after the first migration | **Multi-tenant SaaS from the beginning**, workspace-centric. `User → Workspace → Research Project → Research Session → Opportunity`. `workspace_id` on every primary domain resource. Auth and authz explicitly out of scope; only the contracts that let them be added without a migration | **RESOLVED** | [ADR-005](adr/ADR-005-workspace-multi-tenancy.md) |
| **C-02** | Claims taxonomy: 4 categories in the ontology, 5 in the evidence framework, different casing | **Five canonical UPPERCASE values**: `OBSERVED`, `INFERRED`, `PREDICTED`, `RECOMMENDED`, `HYPOTHESIS`. `HYPOTHESIS` is mandatory and first-class. Closed enum | **RESOLVED** | [`opportunity-ontology-v1.1.md`](../domain/opportunity-ontology-v1.1.md) §7; identical to `evidence-confidence-framework-v1.md` §8 |
| **C-04** | `confidence` was `0–100` in the scoring framework and `0–1` in the evidence framework | **Confidence, reliability, independence, probability on `[0.0, 1.0]`** in storage, contracts and ML; presented as a percentage. **Scores keep `0–100`**. `evidence_level` stays integer `0–5`. Score, confidence, probability and evidence strength are four distinct quantities | **RESOLVED** | [`scoring-framework-v1.1.md`](../domain/scoring-framework-v1.1.md) §4.1 |
| **D-09** | `Owner: Speekyx` was a name, not a verified GitHub handle. `CODEOWNERS` used a placeholder | **The GitHub owner is `@Speekyx`.** All `CODEOWNERS` entries updated; syntax validated | **RESOLVED** | [`CODEOWNERS`](../../CODEOWNERS); `quality-gates.md` §6 |
| **D-04** | No LLM provider, model tier or cost budget chosen. Blocked `nlp` and `execution` | **Provider-agnostic LLM Gateway.** No business service imports a provider SDK. Logical tiers `FAST_MODEL` / `BALANCED_MODEL` / `STRONG_MODEL` / `EMBEDDING_MODEL`. Claude for strong reasoning, Gemini for cheap volume, local BGE-M3 for embeddings, others pluggable. **No hard-coded model names** — configuration only. Cost ladder formalized and measured | **RESOLVED** (architecture; budget *figures* remain Mission 0.2 config) | [ADR-006](adr/ADR-006-provider-agnostic-llm-gateway.md) |
| **D-10** | No environment topology or hosting target. Blocked `infrastructure/` | **Local-first with Docker Compose.** No Kubernetes, no cloud-specific architecture. Production deferred to a future ADR. Eight binding portability rules keep every option open | **RESOLVED** (foundation phase) | [ADR-007](adr/ADR-007-local-first-docker-compose-deployment.md) |
| **D-06** | No retention or deletion policy. Blocked schema design and carried legal exposure | **Raw content 30 days. Normalized observations and evidence 12 months maximum target. Aggregates longer where lawful. Scores versioned and retained.** Per-source `retention_override` with a recorded `basis`. Stricter constraint always wins. Deletion semantics defined; deletion logic not implemented | **RESOLVED** (policy) | [`data-retention-policy-v1.md`](../data/data-retention-policy-v1.md) |

Every row ends `RESOLVED`. No decision in this mission's brief was left unapplied.

---

## 2. Consequential changes

Changes that followed from the decisions above rather than being decisions in
their own right.

| Change | Reason |
|--------|--------|
| `PROJECT_MANIFEST.md` → v1.1, with a version history section | BullMQ removed, Celery added, tenancy declared, authoritative chain repointed |
| `docs/CLAUDE.md` → v1.1, with a §Canonical invariants section | The operating contract must carry the settled invariants, and it was authoritative but unversioned (audit §4 rec. 8) |
| `opportunity-ontology-v1.md` and `scoring-framework-v1.md` marked **superseded**, retained | `docs/CLAUDE.md` §Versioning: a superseded version is never deleted |
| Boot sequence repointed to V1.1 in the manifest, `docs/CLAUDE.md`, `docs/README.md` and the root `README.md` | Future sessions must read the current specifications |
| All backend service READMEs: runtime Python, Celery, `workspace_id`, LLM Gateway | Consequence of ADR-004, ADR-005, ADR-006 |
| Four diagrams updated | A stale diagram is worse than no diagram: it is confidently wrong |
| `service-boundaries.md` → v1.1: runtimes, tenant-scoped data ownership, two new cross-cutting contracts | Consequence of ADR-004, ADR-005, ADR-006 |
| `quality-gates.md` and `testing-strategy.md` → v1.1 | New automated checks (tenancy, numeric scales, idempotency under duplicate delivery) |
| `specification-audit.md` gains a **§6 resolution appendix**; §1–§5 untouched | Instruction §14: do not rewrite original findings |
| A stray `</content>` artifact removed from the end of `specification-audit.md` | File-write defect from Mission 0.1. Not a finding, not content |

---

## 3. Deliberately NOT resolved

Recorded here so nobody mistakes silence for permission.

| ID | Item | Why it stays open |
|----|------|-------------------|
| **D-03 / A-02 / A-03 / A-04** | Evidence aggregation formula, recency decay parameters, independence thresholds, contradiction penalties | **Explicitly forbidden by the Mission 0.1.1 brief §13.** This is the project's hardest blocker: `services/scoring` cannot be implemented until `docs/domain/evidence-aggregation-framework-v1.md` exists and is authorized (`scoring-framework-v1.1.md` §13) |
| **D-01 / A-06** | `ResearchContext` entity | Ontology V2. The brief §7 restricted V1.1 to the taxonomy and scale corrections; adding an entity would have exceeded the authorization |
| **A-11** | "research run" vs "Research Session" vs `ResearchContext` — three names for adjacent concepts | **New in this mission.** An ambiguity, not a contradiction, so work continued. Belongs with D-01 in ontology V2 |
| **D-07** | Source registry and per-source legal review records | Blocks `acquisition`, and blocks the `retention_override` mechanism the retention policy depends on |
| **D-08** | Score recomputation policy — immutable snapshots or recomputed on new evidence? | Interacts with retention: a score outlives its evidence |
| **D-11** | Observability stack | Conventions in `packages/observability` are fixed regardless of the choice |
| **D-12** | Embedding model versioning and re-embedding strategy | Made tractable by ADR-006 model-version tracking, still undecided |
| **A-01** | Sparse vs dense scoring-profile weight vectors | Sparse map recommended, not authorized |
| **A-05** | Geographic scope granularity | `MarketScope` discriminated union recommended, to be fixed in `packages/contracts` |
| **A-07** | Which ontology lists are closed enums vs open registries | Only `ClaimType` is now explicitly closed |
| **A-08** | `MONEY` motivation vs `MONEY_MAKING` value proposition overlap | Documentation-level fix; outside the authorized V1.1 scope |
| — | GDPR/jurisdiction analysis | **Requires human or legal input.** Deliberately not guessed (`data-retention-policy-v1.md` §7) |
| — | Concrete per-run and per-workspace LLM budget figures | Configuration decision for Mission 0.2 |
| — | Production deployment target | Deferred by ADR-007 to a future ADR |

---

## 4. How to use this register

1. **Before implementing:** find the concern here. If it is in §1, the governing
   document is authoritative — follow it, do not re-derive it.
2. **If it is in §3:** stop. Do not choose a value. Record the blockage and raise
   it, per `docs/CLAUDE.md` §Change control.
3. **If it is in neither:** it may be genuinely new. Add it to
   `specification-audit.md` with an id rather than resolving it in code.

The register is append-only in spirit: a row that moves from §3 to §1 records
which ADR or specification moved it, and when.

---

## 5. Superseded by Mission 0.1.2

**Appended 2026-08-27. Sections §1–§4 above are unchanged** and record what was
true at the end of Mission 0.1.1.

Six items listed as open in §3 have since been resolved by
**Opportunity Ontology V2**. The rows above are not rewritten; this section is the
forwarding address.

| ID | §3 status at 0.1.1 | Status now | Governing document |
|----|--------------------|-----------|--------------------|
| **D-01** | Open — ontology V2 | **RESOLVED** | Ontology V2 §11.3 |
| **A-06** | Open — ontology V2 | **RESOLVED** | Ontology V2 §11.3 |
| **A-11** | Open — new in 0.1.1 | **RESOLVED** | Ontology V2 §11, §11.5 |
| **A-05** | Open | **RESOLVED** | Ontology V2 §4 |
| **A-07** | Open | **RESOLVED** | Ontology V2 §14 |
| **A-08** | Open | **RESOLVED** | Ontology V2 §13 |

Still open from §3, unchanged: **D-03 / A-02 / A-03 / A-04** (hard blocker),
**D-07**, **D-08**, **D-11**, **D-12**, **A-01**, GDPR/jurisdiction analysis, LLM
budget figures, production deployment target.

New since: **A-12** (non-geographic scoping) — see
[`mission-0.1.2-decisions.md`](mission-0.1.2-decisions.md) §4.

Full detail: [`mission-0.1.2-decisions.md`](mission-0.1.2-decisions.md).
