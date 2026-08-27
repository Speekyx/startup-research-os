# `infrastructure/scripts` — Operational scripts (planned)

**Status:** not implemented.

## Purpose

Repeatable operational tasks. A task that is performed more than twice becomes a
script here; a task performed by pasting commands from a chat log is a task that
will eventually be performed wrong.

## Planned scripts

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
