# `docs/` — Documentation

Documentation is production code (`PROJECT_MANIFEST.md` §Repository Philosophy).
A behavior change without the corresponding documentation change is an
incomplete change.

## Layout

| Directory | Contents | Authority |
|-----------|----------|-----------|
| `domain/` | Ontology, scoring, evidence frameworks | **Authoritative** (ontology V2, scoring V1.1) |
| `ai/` | LLM reasoning rules | **Authoritative** |
| `data/` | Data principles and retention policy | **Authoritative** |
| `architecture/` | Audit, boundaries, diagrams, ADRs, quality gates | Derived; ADRs are authoritative |
| `CLAUDE.md` | Operating contract for agents and contributors | **Authoritative** (v1.2) |

## Authority

`PROJECT_MANIFEST.md` §Authoritative Documents lists seven documents that define
the project. Nothing in `architecture/` overrides them. If a document in
`architecture/` contradicts an authoritative specification, the specification
wins and the architecture document is a bug.

Where the architecture documents *recommend* a change to a specification (the
audit does, in several places), that recommendation is not in force until the
specification is explicitly versioned and updated
(`docs/CLAUDE.md` §Change control).

## Boot sequence

Read in this order before any non-trivial task:

1. `PROJECT_MANIFEST.md`
2. `docs/CLAUDE.md`
3. `docs/domain/opportunity-ontology-v2.md`
4. `docs/domain/scoring-framework-v1.1.md`
5. `docs/domain/evidence-confidence-framework-v1.md`
6. `docs/ai/llm-reasoning-rules.md`
7. `docs/data/data-principles.md`
8. `docs/data/data-retention-policy-v1.md`
9. Relevant ADRs
10. Task-specific specifications

`opportunity-ontology-v1.md`, `opportunity-ontology-v1.1.md` and
`scoring-framework-v1.md` are **superseded**. They remain as historical records
and must not be used for implementation.

## Versioning

Foundational specifications carry explicit versions in their filename
(`-v1.md`). A material change creates a new version rather than mutating history.

`docs/CLAUDE.md` carries an explicit version as of 1.1, closing the gap recorded
in `specification-audit.md` §4 recommendation 8.

A superseded version is never deleted. It stays in the repository, is marked as
superseded in `PROJECT_MANIFEST.md`, and its successor states in its own §0
exactly what changed and under whose authority.
