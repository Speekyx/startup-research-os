# `infrastructure/docker` — Container images (planned)

**Status:** not implemented. Runtime and deployment posture are now settled
(ADR-004: Python + Celery; ADR-007: local-first Compose), so these images can be
written in Mission 0.2.

## Planned contents

```
docker/
├── python-base.Dockerfile     shared Python 3.12 base
├── api.Dockerfile             FastAPI entrypoint (gateway + orchestrator + analysis)
├── worker.Dockerfile          Celery entrypoint, same codebase as api
├── worker-acquisition.Dockerfile   adds Playwright browser dependencies
├── worker-nlp.Dockerfile      heaviest image: BGE-M3, HDBSCAN
└── web.Dockerfile             Next.js standalone output
```

No Node base image: there is no Node worker tier (ADR-004). The only TypeScript
runtime is `web`.

`api` and `worker` build from the same Python source and differ only in
entrypoint (`service-boundaries.md` §2). Splitting the worker image by queue is
what keeps the Playwright and ML dependency sets from being installed into every
container.

## Build rules

1. **Multi-stage.** Build dependencies never reach the runtime image.
2. **Pinned base images**, by digest where practical.
3. **Non-root runtime user** in every image.
4. **Layer ordering for cache hits**: dependency manifests copied and installed
   before source. Getting this backwards turns a 10-second rebuild into a
   3-minute one on every edit.
5. **No secret in any layer** — not in an `ARG`, not in an intermediate stage.
   Docker history is not a hiding place.
6. **`.dockerignore` per context**, always excluding `node_modules`, `.git`,
   `.env`, test fixtures and local data.

## Known image-specific concerns

**`nlp`** — BGE-M3 weights are large. They are **not** baked into the image
(`.gitignore` already excludes model files): they are mounted or fetched at
startup from object storage, with the model version pinned and recorded for
reproducibility (`llm-reasoning-rules.md` §9). Baking them in makes every image
rebuild a multi-gigabyte operation and couples the model version to the code
version, which breaks D-12 re-embedding.

**`acquisition`** — Playwright requires system browser dependencies. Use the
official Playwright base image rather than hand-assembling the dependency list;
the failure mode of getting it wrong is a browser that launches locally and
crashes in CI.

**`web`** — Next.js `output: "standalone"` to avoid shipping the full
`node_modules`.
