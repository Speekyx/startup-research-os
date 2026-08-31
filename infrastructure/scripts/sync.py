#!/usr/bin/env python3
"""Bring this machine's environment up to the working tree, after a pull.

`git pull` moves four things not at all: the virtualenv, the applied migrations,
the contents of `registry.*`, and `infrastructure/compose/.env`. Each has its own
command, and the failure mode they share is silence -- the code runs, and it runs
against last week's environment. README §After every pull is the prose version of
this file; this is the version that cannot be half-followed.

    python infrastructure/scripts/sync.py
    python infrastructure/scripts/sync.py --check     # report, change nothing
    python infrastructure/scripts/sync.py --verify    # then run every suite

**Stdlib only, and deliberately not run through `uv`** (ADR-009). Installing the
dependencies is one of its steps, so it has to work before they exist.

**It does not touch git.** Pulling is a decision about a branch that may carry
work in progress, and a script that merges on your behalf is a script that will
one day merge something you were not ready for. Pull first, then run this.

It stops at the first step that fails, and every failure names what would fix it.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / "infrastructure/compose/.env"
ENV_TEMPLATE = ROOT / "infrastructure/compose/.env.example"
COMPOSE_FILE = ROOT / "infrastructure/compose/docker-compose.yml"

# The same shapes `check_env_template.py` refuses to see filled in. A key whose
# name says "credential" is never written by this script, whatever the template
# happens to contain.
SECRET_KEY = re.compile(r"(API_KEY|TOKEN|SECRET|PRIVATE_KEY|CREDENTIAL|ACCESS_KEY)$", re.IGNORECASE)

# Keys a machine must answer for itself, even though the template shows a value.
#
# `SROS_USE_PROFILE` is a governance decision, not a setting: it declares what
# this deployment IS, and every source review is assessed against it. The
# template says "There is deliberately NO default" and means it -- copying the
# example value in would let a machine acquire under a profile nobody chose,
# which is the accident the missing default exists to prevent.
NEVER_AUTOFILLED = {"SROS_USE_PROFILE"}


class StepError(Exception):
    """A step that could not complete, carrying what a human should do next."""

    def __init__(self, message: str, remedy: str = "") -> None:
        super().__init__(message)
        self.remedy = remedy


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    """Run a command, streaming its output, and raise if it fails.

    Echoed with the executable's bare name and flushed before the child starts.
    An absolute path to `uv.EXE` is noise, and an unflushed echo appears after
    the output of the command it introduces.
    """
    printable = " ".join([pathlib.Path(command[0]).stem, *command[1:]])
    print(f"  $ {printable}", flush=True)
    proc = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if proc.returncode != 0:
        raise StepError(f"`{printable}` exited {proc.returncode}", printable)


# ------------------------------------------------------------------ the steps


def step_uv(check: bool) -> None:
    """Install the workspace exactly as `uv.lock` pins it.

    `--frozen` on purpose: a sync that silently re-resolved would make two
    machines disagree about what "the same commit" means.
    """
    uv = shutil.which("uv")
    if uv is None:
        raise StepError(
            "uv is not on PATH, and nothing in this repository installs it",
            "winget install --id astral-sh.uv   (then open a NEW terminal: the PATH "
            "of an already-open shell does not change)",
        )
    if check:
        print("  would run: uv sync --all-packages --frozen")
        return
    _run([uv, "sync", "--all-packages", "--frozen"])


def step_services(check: bool) -> None:
    """Start PostgreSQL, Redis and Qdrant.

    Starting them is the easy half. Waiting for them is in `step_database`,
    because `docker compose up -d` returns as soon as the containers exist and a
    migration issued in that window fails with a connection error that reads
    like a configuration problem.
    """
    docker = shutil.which("docker")
    if docker is None:
        raise StepError("docker is not on PATH", "install Docker Desktop")
    if check:
        print(f"  would run: docker compose -f {COMPOSE_FILE.relative_to(ROOT)} up -d")
        return
    try:
        _run([docker, "compose", "-f", str(COMPOSE_FILE), "up", "-d"])
    except StepError as exc:
        raise StepError(
            f"{exc}. The daemon is the usual reason: Docker Desktop must be running",
            "start Docker Desktop, then re-run this script",
        ) from exc


def _wait_for_postgres(url: str, timeout: float = 60.0) -> None:
    """Block until the port accepts a connection, or say what was tried."""
    parsed = urllib.parse.urlparse(url)
    host, port = parsed.hostname or "127.0.0.1", parsed.port or 5432
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"  postgres is accepting connections on {host}:{port}")
                return
        except OSError:
            time.sleep(1.0)
    raise StepError(
        f"postgres did not accept a connection on {host}:{port} within {timeout:.0f}s",
        f"docker compose -f {COMPOSE_FILE.relative_to(ROOT)} logs postgres",
    )


def _parse_env(path: pathlib.Path) -> dict[str, str]:
    """Read a KEY=value file. Values are returned; none of them is printed."""
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip().removeprefix("export ").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def step_env(check: bool) -> dict[str, str]:
    """Reconcile `.env` with the committed template, and return its values.

    The template gains keys as missions add them; a git-ignored `.env` does not,
    and the resulting failure arrives much later as a command that refuses to
    run. Keys the template gives a real value are appended here. Keys it leaves
    empty, keys whose name marks them a credential, and the ones in
    NEVER_AUTOFILLED are reported instead: this script has no business inventing
    a secret, and no standing to make a governance decision.
    """
    if not ENV_FILE.exists():
        raise StepError(
            f"{ENV_FILE.relative_to(ROOT)} does not exist",
            f"cp {ENV_TEMPLATE.relative_to(ROOT)} {ENV_FILE.relative_to(ROOT)}",
        )

    template, current = _parse_env(ENV_TEMPLATE), _parse_env(ENV_FILE)
    missing = [key for key in template if key not in current]

    fillable = [
        key
        for key in missing
        if template[key] and not SECRET_KEY.search(key) and key not in NEVER_AUTOFILLED
    ]
    manual = [key for key in missing if key not in fillable]

    if not missing:
        print("  .env has every key the template declares")
    else:
        print(f"  {len(missing)} key(s) in the template are absent from .env")

    if fillable and check:
        print(f"  would add from the template: {', '.join(fillable)}")
    elif fillable:
        with ENV_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"\n# Added by sync.py from {ENV_TEMPLATE.name}\n")
            for key in fillable:
                handle.write(f"{key}={template[key]}\n")
        print(f"  added from the template: {', '.join(fillable)}")
        current.update({key: template[key] for key in fillable})

    if manual:
        lines = []
        for key in manual:
            if key in NEVER_AUTOFILLED:
                why = "a decision this machine makes, never copied from the example"
            elif SECRET_KEY.search(key):
                why = "a credential; only you have it"
            else:
                why = "the template leaves it empty"
            lines.append(f"    {key}  -- {why}")
        raise StepError(
            "some keys cannot be filled in automatically:\n" + "\n".join(lines),
            f"add them to {ENV_FILE.relative_to(ROOT)}; "
            f"{ENV_TEMPLATE.relative_to(ROOT)} documents each one",
        )
    return current


def step_database(env: dict[str, str], check: bool) -> None:
    """Apply migrations, then load the source catalog into `registry.*`.

    Both are idempotent, and neither grants anything: `migrate.py` skips what is
    already applied, and `load_catalog_into` writes `collector_enabled = FALSE`
    unconditionally. On an up-to-date machine this is a no-op that says so.
    """
    uv = shutil.which("uv")
    if uv is None:  # pragma: no cover - step_uv refused first
        raise StepError("uv is not on PATH", "winget install --id astral-sh.uv")
    if check:
        print("  would run: migrate.py --apply, then sros-source load")
        return

    # The scripts read `os.environ`; they do not read the file. This is the step
    # people skip by hand, and it is why `DATABASE_URL is not set` is the most
    # common first error on a machine that has just pulled. An exported variable
    # still wins, the same precedence `sros_acquisition.cli._load_local_env` uses.
    merged = {**env, **os.environ}
    _wait_for_postgres(merged.get("DATABASE_URL", ""))
    _run([uv, "run", "python", "infrastructure/scripts/migrate.py", "--apply"], env=merged)
    _run([uv, "run", "sros-source", "load"], env=merged)


def step_verify(env: dict[str, str]) -> None:
    """Run every pytest suite, including both leak checks."""
    uv = shutil.which("uv")
    if uv is None:  # pragma: no cover - step_uv refused first
        raise StepError("uv is not on PATH", "winget install --id astral-sh.uv")
    _run(
        [uv, "run", "python", "infrastructure/scripts/run_pytest_suites.py"],
        env={**env, **os.environ},
    )


# ----------------------------------------------------------------- the driver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bring this machine's environment up to the working tree, after a pull.",
        epilog="It does not run git. Pull first, then run this.",
    )
    parser.add_argument(
        "--check", action="store_true", help="report what would change and change nothing"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="also run every pytest suite once the environment is current",
    )
    args = parser.parse_args(argv)

    # Flushed as they are printed. The two streams are buffered independently,
    # so an unflushed heading arrives AFTER the stderr failure it introduces --
    # which reads as the step having failed before it started.
    try:
        print("[1/4] dependencies", flush=True)
        step_uv(args.check)

        print("[2/4] backing services", flush=True)
        step_services(args.check)

        print("[3/4] environment file", flush=True)
        env = step_env(args.check)

        print("[4/4] database and registry", flush=True)
        step_database(env, args.check)

        if args.verify and not args.check:
            print("\nverifying", flush=True)
            step_verify(env)
    except StepError as exc:
        sys.stdout.flush()
        print(f"\nSTOPPED: {exc}", file=sys.stderr)
        if exc.remedy:
            print(f"  fix it with: {exc.remedy}", file=sys.stderr)
        return 1

    if args.check:
        print("\ncheck complete; nothing was changed")
        return 0
    print("\nthis machine is up to date with the working tree")
    if not args.verify:
        print("verify it with: python infrastructure/scripts/sync.py --verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
