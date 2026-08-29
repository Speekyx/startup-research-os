#!/usr/bin/env python3
"""Guard the boundary between a defined framework and production scoring.

Mission 1.1 §39. D-03 is resolved at the framework level, so the old guard --
"no aggregation vocabulary anywhere" -- is no longer the right rule. The wrong
correction would be to delete it and call anything scoring-related allowed.

This script draws the line that replaces it:

  1. Rejected designs stay forbidden EVERYWHERE. Each name encodes a design the
     framework considered and rejected with a stated reason, so its reappearance
     is a regression rather than an unblocked feature.
  2. Authorised V1 vocabulary is allowed in the REFERENCE package and in the
     canonical contracts, and forbidden in migrations. Defining the framework and
     making production scoring available are separate gates.
  3. No universal half-life constant, anywhere. Framework §9 puts half-lives in
     versioned profiles keyed by claim feature; a module constant would be the
     universal value the framework refuses to invent, and it would WORK, which
     is what makes it dangerous.
  4. No per-source reliability coefficient. Asserted by the absence of every
     registered source id from the aggregation package (§7, §42).
  5. `services/scoring` is still a boundary README, with no implementation.
  6. The shipped reference profile is UNCALIBRATED and carries no half-life.

Zero dependencies, no database, no imports of the package under test. It runs in
the install-free CI job for the reason ADR-009 gives: a broken dependency
environment must never be able to reduce a governance check to nothing.

    python infrastructure/scripts/validate_evidence_aggregation.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = ROOT / "packages/contracts/conformance/cases.json"
REFERENCE_PACKAGE = ROOT / "packages/evidence-aggregation/python/sros_evidence_aggregation"
MIGRATIONS = ROOT / "infrastructure/db/migrations"
CATALOG = ROOT / "docs/data/source-catalog-v1.json"

FRAMEWORK = ROOT / "docs/domain/evidence-aggregation-framework-v1.md"
CALIBRATION_PLAN = ROOT / "docs/domain/evidence-aggregation-calibration-plan-v1.md"
SENSITIVITY = ROOT / "docs/domain/evidence-aggregation-sensitivity-v1.md"
GAP_ANALYSIS = ROOT / "docs/domain/evidence-schema-gap-analysis-v1.md"

# Where the authorised V1 vocabulary is allowed to appear. Everything else is a
# production surface, and a production surface using it would mean scoring had
# started without a calibrated profile.
AUTHORISED_ROOTS = (
    "packages/evidence-aggregation",
    "packages/contracts",
    "docs",
)


def _python_sources(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    checks = 0

    cases = json.loads(CASES.read_text(encoding="utf-8"))["forbidden_fields"]
    rejected = cases["names"]
    authorised = cases["authorised_v1_vocabulary"]["names"]
    half_life_names = cases["universal_half_life"]["forbidden_constant_names"]

    # -- 1: the four documents exist ----------------------------------------
    for label, path in (
        ("framework", FRAMEWORK),
        ("calibration plan", CALIBRATION_PLAN),
        ("sensitivity analysis", SENSITIVITY),
        ("schema gap analysis", GAP_ANALYSIS),
    ):
        if not path.exists():
            errors.append(f"missing {label}: {path.relative_to(ROOT)}")
    if not errors:
        print("ok    the four Mission 1.1 specifications exist")
    checks += 1

    # -- 2: rejected designs, forbidden everywhere --------------------------
    offenders: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        parts = set(path.parts)
        if {".venv", "__pycache__", "node_modules", "scratchpad"} & parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in rejected:
            # The guards themselves, and the tests that exercise them, must be
            # able to name what they forbid.
            if name in text and path.name not in {
                "validate_evidence_aggregation.py",
                "validate_schema.py",
                "validate_source_registry.py",
                "test_conformance.py",
            }:
                offenders.append(f"{path.relative_to(ROOT)}: {name}")
    for path in sorted(MIGRATIONS.glob("*.sql")):
        text = path.read_text(encoding="utf-8")
        for name in rejected:
            if re.search(rf"\b{name}\b", text, re.IGNORECASE):
                offenders.append(f"{path.relative_to(ROOT)}: {name}")
    if offenders:
        errors.append(
            f"rejected aggregation designs reappeared: {offenders}. Each of these names "
            "a design evidence-aggregation-framework-v1.md considered and rejected"
        )
    else:
        print(f"ok    no rejected aggregation design present ({len(rejected)} names checked)")
    checks += 1

    # -- 3: authorised vocabulary stays out of production surfaces ----------
    leaked: list[str] = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        text = path.read_text(encoding="utf-8")
        for name in authorised:
            if re.search(rf"\b{name}\b", text, re.IGNORECASE):
                leaked.append(f"{path.relative_to(ROOT)}: {name}")
    for path in sorted((ROOT / "services").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in authorised:
            if re.search(rf"\b{name}\b", text):
                leaked.append(f"{path.relative_to(ROOT)}: {name}")
    if leaked:
        errors.append(
            f"authorised V1 aggregation vocabulary reached a production surface: {leaked}. "
            "The framework being defined does not make production scoring available "
            "(evidence-aggregation-framework-v1.md §14); it is allowed in "
            f"{', '.join(AUTHORISED_ROOTS)} only"
        )
    else:
        print(
            f"ok    V1 aggregation vocabulary confined to the reference package "
            f"({len(authorised)} names checked)"
        )
    checks += 1

    # -- 4: no universal half-life constant ---------------------------------
    half_life_offenders: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        parts = set(path.parts)
        if {".venv", "__pycache__", "node_modules", "scratchpad"} & parts:
            continue
        if path.name == "validate_evidence_aggregation.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in half_life_names:
            if re.search(rf"^\s*{name}\s*[:=]", text, re.MULTILINE):
                half_life_offenders.append(f"{path.relative_to(ROOT)}: {name}")
    if half_life_offenders:
        errors.append(
            f"a universal half-life constant was declared: {half_life_offenders}. "
            "A half-life belongs to a versioned profile keyed by claim feature "
            "(evidence-aggregation-framework-v1.md §9); a constant would be the "
            "invented universal value, and it would work"
        )
    else:
        print("ok    no universal half-life constant (§9 holds mechanically)")
    checks += 1

    # -- 5: no per-source reliability coefficient ---------------------------
    if not CATALOG.exists():
        warnings.append("source catalog absent; per-source weight check skipped")
    else:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        source_ids = [s["source_id"] for s in catalog["sources"]]
        named: list[str] = []
        for path in _python_sources(REFERENCE_PACKAGE):
            lowered = path.read_text(encoding="utf-8").lower()
            for source_id in source_ids:
                if source_id in lowered:
                    named.append(f"{path.name}: {source_id}")
        if named:
            errors.append(
                f"the aggregation package names registered sources: {named}. Reliability "
                "is a property of an evidence record against a claim, never of the "
                "platform (framework §3), and a source's POLICY status is not its "
                "epistemic reliability (§42)"
            )
        else:
            print(
                f"ok    no registered source named in the aggregation package "
                f"({len(source_ids)} ids checked)"
            )
    checks += 1

    # -- 6: services/scoring is still a boundary, not an implementation -----
    #
    # The directory exists and holds a README describing the context, exactly as
    # every other unimplemented context does. What must not exist is CODE: the
    # check is for an implementation, not for a folder.
    scoring = ROOT / "services" / "scoring"
    implementation = (
        [p for p in scoring.rglob("*") if p.is_file() and p.suffix in {".py", ".sql", ".toml"}]
        if scoring.exists()
        else []
    )
    if implementation:
        errors.append(
            f"services/scoring has an implementation: {[str(p.relative_to(ROOT)) for p in implementation]}. "
            "The framework is defined but no CALIBRATED profile exists, so production "
            "scoring remains unavailable (evidence-aggregation-framework-v1.md §14)"
        )
    else:
        print("ok    services/scoring is a boundary only (production scoring stays blocked)")
    checks += 1

    # -- 7: the shipped profile is uncalibrated and carries no half-life ----
    profile_source = REFERENCE_PACKAGE / "profile.py"
    if not profile_source.exists():
        errors.append("the reference profile module is missing")
    else:
        text = profile_source.read_text(encoding="utf-8")
        block = text[text.find("REFERENCE_PROFILE_V1 =") :]
        if "AggregationProfileStatus.UNCALIBRATED" not in block:
            errors.append(
                "REFERENCE_PROFILE_V1 is no longer UNCALIBRATED. Promotion to CALIBRATED "
                "requires the calibration plan to have been executed against a real "
                "labelled dataset, and its evaluation published"
            )
        if re.search(r"half_life_days\s*=\s*MappingProxyType\(\{\s*\}\)", block) is None:
            errors.append(
                "REFERENCE_PROFILE_V1 declares a half-life. §19 forbids inventing one; "
                "an authorised value comes from calibration, in its own profile version"
            )
        if not errors:
            print("ok    reference profile is UNCALIBRATED with no half-life (§9, §14)")
    checks += 1

    # -- report -------------------------------------------------------------
    for warning in warnings:
        print(f"warn  {warning}")
    if errors:
        print("", file=sys.stderr)
        for error in errors:
            print(f"FAIL  {error}", file=sys.stderr)
        return 1

    print()
    print(f"evidence aggregation guard passed: {checks} checks, {len(warnings)} warning(s)")
    print("framework defined; parameters NOT calibrated; production scoring blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
