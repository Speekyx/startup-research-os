# `docs/ai/` — AI and LLM specifications

**Authoritative.**

| Document | Defines |
|----------|---------|
| `llm-reasoning-rules.md` | The role of LLMs, evidence hierarchy, required behavior, structured outputs, tool use, injection handling, cost discipline, reproducibility, evaluation |

## The one-sentence version

**LLMs are reasoning components, not sources of truth.**

Everything else follows from that. An LLM opinion is never market evidence; when
evidence is insufficient the output is a hypothesis, not an invented fact; and a
fluent answer is not a correct answer.

## The three rules most likely to be broken under time pressure

1. **The cost ladder** (§8): rules → classical NLP → embeddings → LLM. An LLM
   call per collected record is a design error, not an optimization opportunity.
   This is the rule that decides whether the system is economically viable at
   volume.
2. **Prompt injection** (§7): scraped content is untrusted data. It never occupies
   a position where it can be read as an instruction. `acquisition` collects
   adversarial text by design — this is not a hypothetical threat model.
3. **Reproducibility** (§9): model, version, prompt version, parameters, inputs,
   timestamp — stored with every output. Without it, a model upgrade silently
   invalidates every historical signal with no way to tell which ones.

## Provider access — ADR-006

**D-04 is resolved.** All LLM access goes through a provider-agnostic **LLM
Gateway**. No business service imports a provider SDK.

Services request a **logical tier**, never a model name:

```text
FAST_MODEL | BALANCED_MODEL | STRONG_MODEL | EMBEDDING_MODEL
```

Initial strategy: Claude for high-quality reasoning, Gemini for cheap
high-volume work, local BGE-M3 for embeddings; OpenAI, OpenRouter and local
providers pluggable. Model names live in configuration, not in code — models
change faster than release cycles.

The gateway is where the three rules above are enforced **once**: the cost ladder
is measured there, reproducibility metadata is attached there, and
structured-output validation (including treating a schema failure as a possible
injection attempt) happens there. Implemented per call site, each of them is one
hurried commit from being skipped.

## Still open

- Concrete per-run and per-workspace cost budget **figures** — a configuration
  decision for Mission 0.2.
- **D-12** — embedding model versioning and the re-embedding strategy when the
  model changes.
- Evaluation datasets (`llm-reasoning-rules.md` §10) — required before any LLM
  component is trusted.
