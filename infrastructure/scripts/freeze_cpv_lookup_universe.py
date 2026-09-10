"""Mission 1.82 §3. Freeze the CPV codes a semantic lookup may ask about, before it asks.

**The universe comes from held codes, not from semantic attractiveness.** Which concepts
this mission is allowed to look up is decided here, from the held division-92 procurement
records alone, and frozen with a digest -- so a label that reads well cannot add a code and
a label that reads badly cannot remove one. The artifact carries **no labels**, by
construction: it is written before any vocabulary is retrieved.

**The rule is the extractor's own, not a second one.** Group and class membership are read
through `ProcurementValueContrastExtractor._cpv_prefix` at grains 3 and 4, the same rule the
derivation will use, so the frozen universe is exactly the set of subjects the held records
can form. A notice whose codes name two subjects at a grain, or none deep enough, joins
none -- and contributes no code to the universe at that grain.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/freeze_cpv_lookup_universe.py

Writes `docs/data/cpv-semantic-lookup-universe-v1.json` and prints its digest. Re-running it
over unchanged held records reproduces the same bytes and the same digest.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "signal-model", "contracts"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))
sys.path.insert(0, str(ROOT / "services" / "acquisition" / "python"))
sys.path.insert(0, str(ROOT / "services" / "nlp" / "python"))

DOCS = ROOT / "docs" / "data"
OUT = DOCS / "cpv-semantic-lookup-universe-v1.json"

DIVISION = "92"
GROUP_GRAIN = 3
CLASS_GRAIN = 4


def main() -> int:
    import psycopg
    from sros_nlp.extractors import EXTRACTOR_REGISTRY
    from sros_nlp.extractors.procurement_value_contrast import CPV_LEVELS
    from sros_nlp.repositories import read_normalized_observations

    workspace_id = os.environ["DEV_WORKSPACE_ID"]
    extractor = EXTRACTOR_REGISTRY["procurement-value-contrast"]

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('sros.workspace_id', %s, true)", (workspace_id,))
            cur.execute(
                """SELECT count(*) FROM acquisition.normalized_records
                    WHERE workspace_id = %s AND record_kind_id = %s AND superseded_at IS NULL""",
                (workspace_id, extractor.record_kind_id),
            )
            total = int(cur.fetchone()[0])
        observations = read_normalized_observations(
            conn,
            workspace_id,
            record_kind_id=extractor.record_kind_id,
            limit=total or 1,
        )

    population = [
        o
        for o in observations
        if any(
            str(entry.get("code", "")).startswith(DIVISION)
            for entry in (o.section("classification").get("codes") or [])
            if isinstance(entry, dict)
        )
    ]
    groups: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    unresolved = {"group": 0, "class": 0}
    for observation in population:
        prefix = extractor._cpv_prefix(observation, GROUP_GRAIN)
        if prefix is None:
            unresolved["group"] += 1
        else:
            groups[prefix] += 1
        prefix = extractor._cpv_prefix(observation, CLASS_GRAIN)
        if prefix is None:
            unresolved["class"] += 1
        else:
            classes[prefix] += 1

    body = {
        "$comment": (
            "Mission 1.82 §3. The EXACT set of CPV concepts a bounded first-party vocabulary "
            "lookup may ask about, derived from held division-92 procurement records before any "
            "label was retrieved. It carries no labels, deliberately: the codes were chosen by "
            "what the held records classify, and a retrieved label may not add one, remove one, "
            "or send the lookup deeper. Membership is read through the production extractor's "
            "own `_cpv_prefix` rule at each grain -- the same rule the derivation uses -- so a "
            "notice whose codes name two subjects at a grain, or none deep enough, contributes "
            "no code at that grain."
        ),
        "record_version": "1.0.0",
        "mission": "1.82",
        "record_kind": "cpv_semantic_lookup_universe",
        "division": DIVISION,
        "levels": {str(k): v for k, v in CPV_LEVELS.items()},
        "DERIVATION_BASIS": (
            "sros_nlp.extractors.procurement_value_contrast.ProcurementValueContrastExtractor"
            f"._cpv_prefix at grain {GROUP_GRAIN} (group) and {CLASS_GRAIN} (class), over every "
            "held, non-superseded procurement_notice NormalizedRecord carrying a CPV code in "
            f"division {DIVISION}"
        ),
        "SOURCE_RECORD_COUNT": len(population),
        "held_procurement_records": total,
        "GROUP_CODES": sorted(groups),
        "CLASS_CODES": sorted(classes),
        "CODE_COUNT_GROUP": len(groups),
        "CODE_COUNT_CLASS": len(classes),
        "notices_per_group_code": dict(sorted(groups.items())),
        "notices_per_class_code": dict(sorted(classes.items())),
        "notices_with_no_group": unresolved["group"],
        "notices_with_no_class": unresolved["class"],
        "labels_present": False,
        "retrieval_performed_before_this_freeze": False,
    }
    rendered = json.dumps(body, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    final = json.dumps({**body, "CONTENT_SHA256": digest}, indent=2, ensure_ascii=False) + "\n"
    OUT.write_text(final, encoding="utf-8", newline="\n")

    print(f"wrote {OUT.name}")
    print(f"  SOURCE_RECORD_COUNT  {len(population)}")
    print(f"  GROUP_CODES  ({len(groups)})  {sorted(groups)}")
    print(f"  CLASS_CODES  ({len(classes)})  {sorted(classes)}")
    print(f"  no group / no class  {unresolved['group']} / {unresolved['class']}")
    print(f"  CONTENT_SHA256  {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
