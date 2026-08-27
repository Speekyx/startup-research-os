# `docs/architecture/` — Architecture documentation

Derived documentation. Nothing here overrides an authoritative specification
(`PROJECT_MANIFEST.md` §Authoritative Documents).

## Contents

| Document | Purpose |
|----------|---------|
| [`specification-audit.md`](specification-audit.md) | Contradictions, ambiguities and missing decisions found in the seven authoritative documents. The running register. §6 and §7 are resolution appendices |
| [`mission-0.1.2-decisions.md`](mission-0.1.2-decisions.md) | **Current resolution register** — what each finding resolved to, and which document governs it now |
| [`mission-0.1.1-decisions.md`](mission-0.1.1-decisions.md) | Predecessor register; §5 forwards the items resolved since |
| [`service-boundaries.md`](service-boundaries.md) | The nine bounded contexts, deployment topology, dependency matrix, data ownership |
| [`quality-gates.md`](quality-gates.md) | What must be true for a change to reach `main` |
| [`testing-strategy.md`](testing-strategy.md) | How to test a system whose output is an estimate |
| [`diagrams/`](diagrams/) | System overview, service communication, data flow, deployment |
| [`adr/`](adr/) | Architecture Decision Records |
| [`mission-0.1-report.md`](mission-0.1-report.md) | Mission 0.1 completion report — **historical, not amended** |
| [`mission-0.1.1-report.md`](mission-0.1.1-report.md) | Mission 0.1.1 completion report — **historical, not amended** |
| [`mission-0.1.2-report.md`](mission-0.1.2-report.md) | Mission 0.1.2 completion report — **historical, not amended** |
| [`mission-0.2-report.md`](mission-0.2-report.md) | Mission 0.2 completion report — **historical, not amended** |
| [`mission-0.3-report.md`](mission-0.3-report.md) | Mission 0.3 completion report — current |

## Start here

- **New to the project?** `service-boundaries.md`, then
  `diagrams/system-overview.md`.
- **About to implement something?** `mission-0.1.2-decisions.md` first, then the
  0.1.1 register — together they tell you what is settled. Then
  `specification-audit.md` §7, which lists what is genuinely still undecided, so
  you do not accidentally decide it by guessing.

  The one hard blocker: **`services/scoring` cannot be implemented** until the
  evidence aggregation framework exists (`scoring-framework-v1.1.md` §13).
- **Making an architectural decision?** `adr/README.md`.

## The audit is a living document

`specification-audit.md` is not a one-time deliverable. When you find a new
ambiguity or contradiction, add it there with an id rather than resolving it in
code. `docs/CLAUDE.md` §Before implementation step 4 requires stating ambiguity
before implementing; this file is where "stating" happens durably.

Missions 0.1.1 and 0.1.2 added **§6 and §7 resolution appendices** to the audit
rather than rewriting the original findings. The findings stay as they were
written: a contradiction that was real and then resolved is more useful history
than a document that reads as though it never existed.

The same rule applies to the registers. `mission-0.1.1-decisions.md` §1–§4 record
what was true at the end of that mission; §5 was appended as a forwarding address
for the six items Ontology V2 has since resolved.
