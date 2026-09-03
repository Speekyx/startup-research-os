"""Mission 1.41 §6, §7. Does the repaired grouping still mean what division 90 meant?

**The mandatory check, and it is run rather than argued.** Adding a field to a
grouping key can only SPLIT groups, never merge them, and every cohort that
derived under 1.0.1 had exactly one currency and one scope because the validation
refused anything else -- so the historical cohort should stay one cohort with the
same members. That is a sound argument and it is not evidence.

This re-derives from the EXACT historical inputs and compares meaning field by
field. §7: Signal UUID equality is NOT required, because the extractor version
participates in deterministic identity and a legitimate version bump moves it.
What must not move is what the observation MEANS.

Read-only. It derives in memory and writes one JSON artifact; nothing is
persisted.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/verify_procurement_grain_reproducibility.py
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import UTC, datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "signal-model", "contracts"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))
sys.path.insert(0, str(ROOT / "services" / "acquisition" / "python"))
sys.path.insert(0, str(ROOT / "services" / "nlp" / "python"))

OUT = ROOT / "docs" / "data" / "procurement-grain-reproducibility-v1.json"

HISTORICAL_SIGNAL = "97ff6d37-1a2d-5725-ad97-d846767b8631"


def main() -> int:
    import psycopg
    from sros_nlp.extractors import EXTRACTOR_REGISTRY
    from sros_nlp.extractors.base import CandidateGroup, DerivationRequest
    from sros_nlp.repositories import read_normalized_observations

    workspace_id = os.environ["DEV_WORKSPACE_ID"]
    extractor = EXTRACTOR_REGISTRY["procurement-value-contrast"]

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('sros.workspace_id', %s, true)", (workspace_id,))
            cur.execute(
                """SELECT magnitude, magnitude_unit, extractor_version, scope, direction
                     FROM nlp.signals WHERE id = %s""",
                (HISTORICAL_SIGNAL,),
            )
            row = cur.fetchone()
            if row is None:
                print(f"REFUSED: historical signal {HISTORICAL_SIGNAL} is not in this deployment")
                return 1
            old = {
                "magnitude": str(row[0]),
                "currency": row[1],
                "extractor_version": row[2],
                "scope": row[3],
                "direction": row[4],
            }
            cur.execute(
                """SELECT normalized_record_id FROM nlp.signal_inputs WHERE signal_id = %s""",
                (HISTORICAL_SIGNAL,),
            )
            input_ids = [str(r[0]) for r in cur.fetchall()]

        observations = read_normalized_observations(
            conn,
            workspace_id,
            record_kind_id=extractor.record_kind_id,
            record_ids=input_ids,
            limit=len(input_ids),
        )

    derivation = extractor.resolve({"amount_type": old["scope"]["amount_types"][0]})
    keys = {extractor.group_key(o, derivation) for o in observations}

    now = datetime.now(UTC)
    request = DerivationRequest(
        workspace_id=workspace_id,
        correlation_id="mission-1.41-reproducibility",
        derived_at=now,
        expires_at=now + timedelta(days=90),
        research_session_id=None,
    )
    group = CandidateGroup(key=sorted(k or "" for k in keys)[0], observations=tuple(observations))
    outcome = extractor.derive(group, derivation, request)

    new: dict[str, object]
    if outcome.drafts:
        draft = outcome.drafts[0]
        new = {
            "magnitude": str(draft.magnitude.value),
            "currency": draft.magnitude.unit,
            "extractor_version": draft.derivation.extractor_version,
            "scope": draft.scope.to_json()
            if hasattr(draft.scope, "to_json")
            else dict(draft.scope),
            "direction": draft.direction.value,
        }
    else:
        new = {"refusals": [r.reason.value for r in outcome.refusals]}

    def field(name: str) -> object:
        return new.get(name) if isinstance(new, dict) else None

    old_scope = old["scope"]
    new_scope = new.get("scope") or {}
    comparison = {
        "historical_signal_id": HISTORICAL_SIGNAL,
        "historical_inputs": len(input_ids),
        "regrouped_into_n_groups": len({k for k in keys if k is not None}),
        "records_with_no_key": sum(1 for k in keys if k is None),
        "magnitude": {"old": old["magnitude"], "new": field("magnitude")},
        "currency": {"old": old["currency"], "new": field("currency")},
        "direction": {"old": old["direction"], "new": field("direction")},
        "amount_types": {
            "old": old_scope.get("amount_types"),
            "new": new_scope.get("amount_types"),
        },
        "amount_scopes": {
            "old": old_scope.get("amount_scopes"),
            "new": new_scope.get("amount_scopes"),
        },
        "classification_codes": {
            "old": old_scope.get("classification_codes"),
            "new": new_scope.get("classification_codes"),
        },
        "notice_ids": {
            "old": old_scope.get("notice_ids"),
            "new": new_scope.get("notice_ids"),
        },
        "extractor_version": {
            "old": old["extractor_version"],
            "new": field("extractor_version"),
        },
    }

    semantic_fields = (
        "magnitude",
        "currency",
        "direction",
        "amount_types",
        "amount_scopes",
        "classification_codes",
        "notice_ids",
    )
    differing = [
        name for name in semantic_fields if comparison[name]["old"] != comparison[name]["new"]
    ]
    reproduced = not differing and comparison["regrouped_into_n_groups"] == 1

    document = {
        "$comment": (
            "Mission 1.41 §6, §7. The historical division-90 Signal, re-derived from its "
            "exact persisted inputs under the repaired 1.1.0 grouping. Signal UUID equality "
            "is deliberately NOT required: the extractor version participates in "
            "deterministic identity, so a legitimate bump moves it. What must not move is "
            "the MEANING, and that is what is compared field by field below. Read-only."
        ),
        "artifact_version": "procurement-grain-reproducibility@1.0.0",
        "generated_by": "mission-1.41",
        "semantically_reproduced": reproduced,
        "differing_fields": differing,
        "comparison": comparison,
    }
    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"historical inputs      : {len(input_ids)}")
    print(f"regrouped into         : {comparison['regrouped_into_n_groups']} group(s)")
    for name in semantic_fields:
        mark = "  " if comparison[name]["old"] == comparison[name]["new"] else "X "
        print(f"{mark}{name:22} old={comparison[name]['old']}")
        print(f"  {'':22} new={comparison[name]['new']}")
    print(f"\nsemantically reproduced: {reproduced}")
    print(f"wrote {OUT.name}")
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
