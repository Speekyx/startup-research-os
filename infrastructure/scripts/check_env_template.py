#!/usr/bin/env python3
"""Fail if a committed environment template carries a populated credential.

The most likely accidental leak in this repository is someone filling in
`.env.example` instead of copying it to `.env`. `.env` is git-ignored;
`.env.example` is committed, so a value typed into it is published.

Stdlib only. Usage: python infrastructure/scripts/check_env_template.py
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Keys that must always be empty in a committed template.
SECRET_KEY = re.compile(r"(API_KEY|TOKEN|SECRET|PRIVATE_KEY|CREDENTIAL|ACCESS_KEY)$", re.IGNORECASE)

# Keys allowed to carry an obvious development placeholder.
DEV_PLACEHOLDER_OK = {"POSTGRES_PASSWORD", "DATABASE_URL"}

# Values that are clearly placeholders rather than real credentials.
PLACEHOLDER = re.compile(
    r"^(|null|changeme|placeholder|\S*_dev_password|.*(localhost|127\.0\.0\.1).*)$",
    re.IGNORECASE,
)


def check(path: pathlib.Path) -> list[str]:
    problems: list[str] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()

        if SECRET_KEY.search(key) and value:
            problems.append(
                f"{path.relative_to(ROOT)}:{number}: {key} has a value. "
                "Committed templates must leave credentials empty."
            )
            continue

        if key in DEV_PLACEHOLDER_OK and not PLACEHOLDER.match(value):
            problems.append(
                f"{path.relative_to(ROOT)}:{number}: {key} does not look like a "
                "development placeholder."
            )
    return problems


def main() -> int:
    templates = sorted(ROOT.rglob(".env.example"))
    templates = [p for p in templates if "node_modules" not in p.parts]

    if not templates:
        print("no .env.example found", file=sys.stderr)
        return 1

    problems: list[str] = []
    for path in templates:
        problems.extend(check(path))
        print(f"checked {path.relative_to(ROOT)}")

    # A real .env must never be COMMITTED. Its presence on a developer machine
    # is normal and expected -- .gitignore covers it -- so the check is against
    # git tracking, not against the filesystem.
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "--", "*.env", "**/.env"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.split()
    except FileNotFoundError:
        tracked = []
        print("note: git not available, skipping tracked-.env check")

    for entry in tracked:
        problems.append(f"{entry}: a real .env file is tracked by git")

    if problems:
        print("\nENVIRONMENT TEMPLATE CHECK FAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"\nok: {len(templates)} template(s), no populated credential")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
