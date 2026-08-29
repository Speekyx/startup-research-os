"""Effective retention, per source.

Mission 1.0 §15, implementing `data-retention-policy-v1.md` §1 and §3.

**One rule decides everything here: the stricter applicable constraint wins.**
§1 states it twice — once for the reproducibility-versus-minimisation conflict
and once for source policy — and it is the rule that makes an override safe to
grant in both directions. A source may shorten retention, and a source that
permits longer retention does not automatically get it: necessity must also be
established, which is a human judgment recorded in `basis` rather than a
calculation.

**Absence of an override is not permission to keep data forever.** With no
source-specific rule, the §2 baseline applies: 30 days for raw content, a
12-month ceiling for normalized observations. A source with no registry entry at
all may not be collected from, which is `data-principles.md` §13 and is enforced
by the eligibility gate rather than here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import RetentionOverride

__all__ = [
    "BASELINE_RAW_DAYS",
    "BASELINE_NORMALIZED_DAYS",
    "EffectiveRetention",
    "resolve_retention",
]

# data-retention-policy-v1.md §2.1 and §2.2. Defaults, not entitlements: §2.2
# calls its figure "a ceiling, not an entitlement", and necessity still applies.
BASELINE_RAW_DAYS = 30
BASELINE_NORMALIZED_DAYS = 365


@dataclass(frozen=True)
class EffectiveRetention:
    """What actually applies to one source, and where each number came from."""

    raw_days: int
    normalized_days: int
    aggregate_permitted: bool
    raw_source: str
    normalized_source: str
    basis: str | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "raw_days": self.raw_days,
            "normalized_days": self.normalized_days,
            "aggregate_permitted": self.aggregate_permitted,
            "raw_source": self.raw_source,
            "normalized_source": self.normalized_source,
            "basis": self.basis,
        }


def resolve_retention(override: RetentionOverride | None) -> EffectiveRetention:
    """Fold an optional override onto the baseline, stricter value winning.

    `min()` is the whole implementation, and it is deliberate: an override that
    asked for *longer* retention than the baseline does not get it from this
    function. Lengthening retention needs necessity established and recorded,
    which §3 makes a reviewed decision rather than an arithmetic one. What this
    function guarantees is that no configuration can quietly extend a retention
    window.
    """
    if override is None:
        return EffectiveRetention(
            raw_days=BASELINE_RAW_DAYS,
            normalized_days=BASELINE_NORMALIZED_DAYS,
            aggregate_permitted=True,
            raw_source="baseline",
            normalized_source="baseline",
        )

    raw_days = BASELINE_RAW_DAYS
    raw_source = "baseline"
    if override.raw_days is not None:
        raw_days = min(BASELINE_RAW_DAYS, override.raw_days)
        raw_source = "source" if raw_days == override.raw_days else "baseline (stricter)"

    normalized_days = BASELINE_NORMALIZED_DAYS
    normalized_source = "baseline"
    if override.normalized_days is not None:
        normalized_days = min(BASELINE_NORMALIZED_DAYS, override.normalized_days)
        normalized_source = (
            "source" if normalized_days == override.normalized_days else "baseline (stricter)"
        )

    return EffectiveRetention(
        raw_days=raw_days,
        normalized_days=normalized_days,
        # A source that forbids retaining aggregates wins over the baseline
        # permission, never the other way round.
        aggregate_permitted=override.aggregate_permitted,
        raw_source=raw_source,
        normalized_source=normalized_source,
        basis=override.basis,
    )
