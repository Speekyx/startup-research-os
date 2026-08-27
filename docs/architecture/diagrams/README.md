# Architecture Diagrams

Mermaid diagrams describing the system as designed in Mission 0.1. They render
natively on GitHub and in most Markdown viewers.

| Diagram | Question it answers |
|---------|---------------------|
| [`system-overview.md`](system-overview.md) | What are the parts and how are they layered? |
| [`service-communication.md`](service-communication.md) | Who calls whom, and what happens during a `ResearchSession`? |
| [`data-flow.md`](data-flow.md) | How does a raw record become a score? |
| [`deployment-view.md`](deployment-view.md) | What actually runs, where? |

## Rules

1. **Diagrams describe the design, not aspirations.** Anything not yet decided is
   marked as pending on the diagram itself, with the decision id (D-0X / ADR-00X).
2. **A diagram that contradicts `service-boundaries.md` is a bug**, and the
   document wins.
3. **Diagrams are updated in the same PR as the change they describe.** A stale
   diagram is worse than no diagram: it is confidently wrong.
4. **No screenshots of diagrams.** Mermaid source only — it diffs, images do not.
