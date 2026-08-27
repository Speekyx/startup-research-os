# ADR-009 — Contract-first domain vocabulary with stdlib code generation

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Implemented in Mission 0.2 under brief §8
- **Supersedes:** none
- **Related:** ADR-001, ADR-003, audit **C-02**, **C-04**, Ontology V2 §14

---

## Context

The system is polyglot by necessity (ADR-003): TypeScript in `apps/web` and
`packages/*`, Python everywhere on the backend. The same domain vocabulary —
claim types, scopes, numeric ranges, session statuses — has to exist in both.

The specification audit already found this failure mode **in the documents**,
before any code existed:

- **C-02** — the claims taxonomy was defined twice with different values.
- **C-04** — `confidence` had two different ranges in two documents.

Both were the same failure: one concept maintained in two places. Two
hand-written type definitions in two languages would reproduce it faster than
prose did, and the symptom would be a silently wrong number rather than a
contradiction someone can read.

So the requirement is not "share some types". It is: **make it impossible for the
TypeScript and Python vocabularies to disagree without a test going red.**

### Constraints discovered during implementation

The foundation must be buildable and checkable in an environment with no
package manager available. During Mission 0.2, neither `pnpm` nor `pydantic`,
`pytest` or a TypeScript compiler were installable. A contract check that cannot
run is a contract check that gets skipped.

## Decision

**A single hand-edited JSON source of truth, plus a stdlib-only Python generator
that emits both language bindings and a JSON Schema.**

```text
packages/contracts/schema/domain.v1.json          source of truth (hand-edited)
                    |
        tools/generate.py  (Python stdlib only)
                    |
      +-------------+-----------------------------+
      |             |                             |
src/generated/   python/sros_contracts/    schema/domain.v1.schema.json
  domain.ts        generated/domain.py       (OpenAPI / interop)
```

Three further rules make the guarantee real:

1. **Generated vocabulary, hand-written behavior.** The generator emits the
   *vocabulary* — enums, numeric bounds, identifier formats, registry names,
   scope rules. Validation and canonicalization are hand-written per language,
   because they are behavior, not data.

2. **A shared conformance suite is the proof.**
   `packages/contracts/conformance/cases.json` is read by **both** the Python
   and the TypeScript test suites. Every case — valid inputs, invalid inputs,
   canonical outputs, equality, canonical JSON — is asserted identically on both
   sides. If the implementations drift, one suite fails.

3. **`--check` mode in CI.** `python tools/generate.py --check` fails when the
   committed output does not match the source. Generation is deterministic
   (sorted keys, stable ordering), so the check is reproducible.

### Why generate a vocabulary rather than full models

Full model generation (Pydantic classes, Zod schemas) sounds stronger and is
weaker here. A generated model can express "confidence is a float in [0,1]". It
cannot express:

- country codes are uppercased, deduplicated and **sorted**, so that one scope
  has one representation and can be used as a cache key;
- `COUNTRY` carries exactly one code while `MULTI_COUNTRY` carries two or more;
- a `ResearchContext` canonical JSON must be **byte-identical** across languages
  so its hash is stable.

Those are the rules that actually matter, and every generator would have left
them to hand-written code anyway — but with the illusion of coverage. Generating
the vocabulary and testing the behavior against shared cases puts the guarantee
where the risk is.

## Alternatives considered

### Alternative A — JSON Schema as source of truth, `json-schema-to-typescript` + `datamodel-code-generator`

The conventional contract-first stack. Rejected for two reasons. It requires two
codegen toolchains in two package managers, so the contract check depends on both
installing correctly — and it still cannot express canonicalization, so the
hand-written layer exists regardless. The JSON Schema is still produced here, as
a *derived artifact* for OpenAPI and interop, which keeps the interop benefit
without the dependency.

### Alternative B — Pydantic models as source of truth, export JSON Schema, generate TS

Natural given a Python-heavy backend, and it would make the backend types
first-class. Rejected: it makes TypeScript a second-class consumer that receives
types with no runtime validation, and it puts the source of truth inside one
runtime's type system, so the frontend can only ever follow. It also makes
`packages/contracts` depend on Pydantic, which every Python consumer then
inherits.

### Alternative C — TypeScript/Zod as source of truth

The mirror image of B, with the mirror problem: the backend, which does most of
the domain work, would follow the frontend's type system.

### Alternative D — Protobuf / Avro IDL

Genuinely good at cross-language contracts. Rejected as disproportionate: it adds
a compiler, a wire format the system does not need (everything here is JSON over
HTTP), and a second schema language to learn, to gain code generation the project
can get from 300 lines of stdlib Python.

### Alternative E — Hand-write both, review carefully

Rejected. This is precisely what produced C-02 and C-04 in the specifications,
with fewer moving parts and more attention than code review will ever get.

## Pros

- **One place to change a domain concept.** Adding a claim type is one edit and a
  regeneration.
- **Drift is a test failure, not a production bug** — the conformance suite is the
  mechanism, and it fails on the language that lagged.
- **Zero dependencies.** The generator and both test suites run with only Python
  and Node installed. A contract check that cannot be skipped for environmental
  reasons is a contract check that runs.
- **JSON Schema falls out for free**, so OpenAPI and third-party tooling stay
  reachable.
- **Explicit versioning.** `contract_version` is carried in the source, both
  outputs and the JSON Schema.
- **Generated files announce themselves.** Each carries a DO-NOT-EDIT banner
  naming the source and the regeneration command.

## Cons

Concretely, because these are the costs accepted:

- **A bespoke generator to maintain.** It is small and stdlib-only, but it is
  code nobody else maintains. If it grows past a few hundred lines, that is the
  signal to revisit Alternative A.
- **Behavior is written twice.** `market_scope.py` and `marketScope.ts` implement
  the same rules independently. The conformance suite catches divergence, but it
  only catches what the cases cover — an uncovered rule can still drift.
- **JSON is a poor authoring format.** No comments (`$comment` keys are a
  workaround), verbose, easy to get a trailing comma wrong. YAML would be nicer
  to write and would add a dependency to the one tool that must never fail to
  run.
- **No compile-time guarantee that the two languages agree** — only a runtime
  test. A stronger scheme (Protobuf) would give the former.
- **Python contracts are stdlib dataclasses, not Pydantic.** Services must adapt
  them at their HTTP boundary (ADR-003 still stands). That adaptation is a small
  amount of glue per service, traded for a contracts package every consumer can
  import for free.

## Future impact

**Becomes easy:** adding or changing a domain concept; keeping the frontend and
backend in step; generating OpenAPI; adding a third language.

**Becomes hard:** expressing complex structural constraints in the source of
truth (they land in hand-written code); guaranteeing agreement without tests.

**Revisit if:** the generator exceeds roughly 500 lines or starts needing a
template engine; or a third consumer language appears, at which point the
hand-written behavior triples and Alternative A or D becomes worth its
dependencies.

**Cost of reversal:** low. The JSON source of truth is already a schema, and the
generated artifacts are replaceable. Swapping to a standard toolchain means
rewriting `generate.py`, not the domain.

## Compliance with authoritative specifications

- **Audit C-02, C-04** — one declaration of every domain enum and scale,
  mechanically shared. This ADR is the structural fix those findings asked for.
- **Ontology V2 §14.3** — registry taxonomies are emitted as *registry names and
  a reference type*, never as generated union types. Enumerating them would
  recreate the migration-per-concept problem the registry split prevents.
- **`scoring-framework-v1.1.md` §4.1** — `NUMERIC_BOUNDS` is generated from one
  place; the naming rule (`confidence` is `[0,1]`, `*_score` is `0–100`) is
  tested on both sides.
- **`scoring-framework-v1.1.md` §13 / D-03** — the conformance suite includes a
  guard test that fails if any aggregation field name appears in the contracts.
  The blocker is enforced by a test, not by memory.
- **Ontology V2 §11.3** — `ResearchContext` canonical JSON is byte-identical
  across languages, which is what makes the session snapshot hash meaningful.
- **ADR-003** — Pydantic remains the rule at service boundaries; the contracts
  package stays dependency-free so every service can consume it.
