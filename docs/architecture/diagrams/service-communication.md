# Service Communication

Two views: the allowed call graph (static), and one `ResearchSession` (dynamic).

> **Updated in Mission 0.1.2.** The persisted execution entity is
> `ResearchSession` (Ontology V2 §11); `research run` is retired. Endpoints and
> correlation fields use the canonical names.
>
> **Updated in Mission 0.1.1.** Queue is Celery over Redis (ADR-004). Every call
> and every task payload carries `workspace_id` (ADR-005).

---

## 1. Allowed call graph

Solid = synchronous call. Dashed = asynchronous message.
Anything not drawn is forbidden (`service-boundaries.md` §4).

```mermaid
graph LR
    WEB["apps/web"]
    GW["gateway"]
    RO["research-orchestrator"]
    Q{{"Celery / Redis"}}
    WK["workers"]
    ACQ["acquisition"]
    NLP["nlp"]
    SCO["scoring"]
    MI["market-intelligence"]
    COMP["competition"]
    EXEC["execution"]

    WEB -->|HTTP /v1| GW
    GW -->|HTTP /internal| RO
    GW -->|HTTP /internal| SCO
    GW -->|HTTP /internal| MI
    GW -->|HTTP /internal| COMP
    GW -->|HTTP /internal| EXEC

    RO -.enqueue.-> Q
    Q -.consume.-> WK
    WK -.progress.-> RO

    WK --> ACQ
    WK --> NLP
    WK --> SCO
    WK --> MI
    WK --> COMP
    WK --> EXEC

    SCO --> NLP
    SCO --> MI
    SCO --> COMP
    MI --> NLP
    COMP --> NLP
    COMP --> MI
    EXEC --> SCO
    EXEC --> MI
    EXEC --> COMP

    RO -->|evidence sufficiency| SCO
```

### Invariants visible here

- `apps/web` has exactly one outgoing edge.
- `acquisition` and `nlp` have **no outgoing edges** to other contexts.
- Nothing calls `workers`. Work enters through the queue.
- `gateway` has no path to `acquisition`, `nlp` or `workers`.
- The graph is acyclic. `workers -.progress.-> research-orchestrator` is the only
  back edge, and it is events only.

---

## 2. One ResearchSession

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant WEB as apps/web
    participant GW as gateway
    participant RO as research-orchestrator
    participant Q as Celery / Redis
    participant WK as workers
    participant ACQ as acquisition
    participant NLP as nlp
    participant MI as market-intelligence
    participant CO as competition
    participant SC as scoring
    participant EX as execution

    U->>WEB: define ResearchContext (within a ResearchProject)
    WEB->>GW: POST /v1/research-sessions
    GW->>RO: create session (workspace_id + project_id + ResearchContext)
    RO->>RO: snapshot context, build plan, assign budget
    RO->>Q: enqueue acquire.source jobs
    GW-->>WEB: 202 research_session_id (status: PLANNING)

    Note over RO,Q: The HTTP request is already finished.<br/>Cost is bounded by the run budget, not by the request.

    Q->>WK: acquire.source
    WK->>ACQ: collect
    ACQ-->>WK: raw + normalized records (with provenance)
    WK-->>RO: progress

    alt source unavailable or rate limited
        ACQ-->>WK: failure + reason
        WK-->>RO: record research gap
        Note over RO: Run continues.<br/>Research Completeness decreases.<br/>No fabricated substitute.
    end

    RO->>Q: enqueue nlp.extract / nlp.embed / nlp.cluster
    Q->>WK: nlp jobs
    WK->>NLP: extract, embed, cluster, estimate independence
    NLP-->>WK: signals + classifications + opportunity seeds
    WK-->>RO: progress

    RO->>Q: enqueue market.analyze + competition.map
    Q->>WK: analysis jobs
    WK->>MI: market context for scope
    WK->>CO: competitors + Competition Gap
    MI-->>WK: market intelligence (evidence + confidence)
    CO-->>WK: competition analysis (evidence + confidence)

    RO->>SC: evidence sufficiency check
    SC-->>RO: sufficiency report

    alt evidence insufficient and budget remains
        RO->>Q: enqueue targeted deep research
        Note over RO: Selective depth.<br/>Depth follows signal, it is not applied uniformly.
    end

    RO->>Q: enqueue score.opportunity
    Q->>WK: scoring job
    WK->>SC: compute five score families
    SC-->>WK: scores + components + rationale + versions

    RO->>Q: enqueue execution.plan
    Q->>WK: planning job
    WK->>EX: MVP + GTM plan
    EX-->>WK: plan (all claims RECOMMENDED / PREDICTED)

    RO->>RO: finalize, compute Research Completeness
    WEB->>GW: GET /v1/research-sessions/{id}
    GW->>RO: session status
    GW-->>WEB: COMPLETED + coverage gaps
    U->>WEB: inspect opportunity
    WEB->>GW: GET /v1/opportunities/{id}/evidence
    Note over WEB,GW: Every score is one interaction<br/>from its evidence.
```

### Three things this sequence encodes deliberately

1. **The HTTP request returns before the work starts** (step 6). A synchronous
   session would put an unbounded LLM bill behind a user clicking a button.

2. **A failed source is a recorded gap, not a run failure.** The run continues
   with lower Research Completeness. The alternative — silently continuing as if
   coverage were complete — inflates every downstream confidence value.

3. **Evidence sufficiency is checked before scoring, and can trigger more
   research.** This is the loop that makes `Research Completeness` meaningful:
   something in the system compares intended coverage against actual coverage and
   can act on the difference.

4. **The queue is Celery over Redis, and delivery is at-least-once** (ADR-004).
   Every `Q->>WK` arrow above may fire twice for the same logical work. That is
   not an edge case to handle later: it is the normal contract, and every job
   body must be idempotent for the sequence above to be correct.

5. **`workspace_id` travels the whole sequence.** It enters at the gateway,
   rides in every task payload, and is written on every row produced. No
   participant below the gateway resolves it independently — a worker that could
   look up "the current workspace" could look up the wrong one (ADR-005).

6. **The `ResearchContext` is snapshotted at step 4, not referenced.** Editing the
   project's context afterwards must not retroactively change what this session
   says it ran with. That immutability is the whole reason the snapshot exists
   (Ontology V2 §11.3).

7. **Reaching `COMPLETED` does not mean full coverage.** A session that exhausts
   its budget or loses a source still completes, with recorded gaps and a lower
   Research Completeness. `FAILED` means the research could not run, not that the
   market was empty (Ontology V2 §15).
