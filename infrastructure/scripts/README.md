# `infrastructure/scripts` — Operational scripts

**Status:** in use. Sixteen scripts run here, and CI runs most of them
(`.github/workflows/ci.yml`). They are Python rather than the `sh` originally
planned below, because they parse SQL, JSON and the source catalog.

## Purpose

Repeatable operational tasks. A task that is performed more than twice becomes a
script here; a task performed by pasting commands from a chat log is a task that
will eventually be performed wrong.

## After a pull, on any machine

```bash
python infrastructure/scripts/sync.py
```

`sync.py` is the executable form of README §After every pull. It installs the
locked dependencies, starts the backing services, reconciles
`infrastructure/compose/.env` against the committed template, applies migrations
and reloads the source catalog into `registry.*` — the four things `git pull`
does not move. It stops at the first step that fails and names the fix.

It is stdlib-only and is deliberately NOT run through `uv`, because installing
the dependencies is one of its own steps. `--check` reports without changing
anything; `--verify` follows with every pytest suite.

Two things it will not do, both on purpose. **It never runs git**, so it cannot
merge anything on a branch carrying work in progress. And it never writes a key
whose name marks it a credential, nor `SROS_USE_PROFILE` — the first is a secret
only the operator has, the second is a governance decision, and the template
says it has deliberately no default. Both are reported for a person to answer.

## Planned scripts

`sync.py` covers what `bootstrap-local.sh` and `verify-env.sh` were for. The
rest remain unwritten.

| Script | Purpose |
|--------|---------|
| `bootstrap-local.sh` | Full local setup: deps, backing services, migrations, seed |
| `db-migrate.sh` | Apply migrations |
| `db-reset.sh` | Drop and recreate the local database. **Local only** — must refuse to run against a non-local host |
| `qdrant-reindex.sh` | Rebuild the vector index from PostgreSQL (safe because Qdrant is derived — audit A-09) |
| `check-secrets.sh` | Scan the working tree for credential patterns before commit |
| `verify-env.sh` | Verify required environment variables and tool versions |
| `seed-workspace.sh` | Create the default development workspace (ADR-005) |
| `retention-preview.sh` | Report what the retention policy *would* expire, without deleting |

## Rules

1. **POSIX `sh` or `bash`**, with `set -euo pipefail`. A script that continues
   after a failed step is worse than no script.
2. **Idempotent.** Running twice is safe.
3. **Destructive scripts refuse by default** and require an explicit
   `--yes` plus an environment check. `db-reset.sh` must be structurally unable
   to run against production.
   The same applies to anything implementing deletion under
   `data-retention-policy-v1.md`: dry-run is the default, deletion is opt-in, and
   every deletion is recorded (§5.2).
4. **No secret in any script.** Read from the environment.
5. **Every script has a `--help`.**
6. **Windows-friendly** — contributors are on Windows (`.gitattributes` keeps
   `.sh` at LF; a CRLF shell script fails with an unhelpful error).
