"""The versioned parameter set, and its calibration status.

Mission 1.1 §20, §21, §41.

Two things move independently and must be versioned independently:

    algorithm_version   the equations       -- defined by Mission 1.1
    profile version     the parameters      -- NOT calibrated by Mission 1.1

Conflating them is how a system ends up unable to say whether a result changed
because the mathematics changed or because someone edited a half-life.

**A defined framework is not a calibrated one.** The equations in this package
were derived from stated requirements, not fitted to outcomes. No labelled
dataset exists, so no parameter in `REFERENCE_PROFILE_V1` was measured. Its
status is `UNCALIBRATED` and it will stay that way until
`evidence-aggregation-calibration-plan-v1.md` has actually been executed against
real labelled data — which is a future mission, not a formality.

That is why `half_life_days` is **empty**. A temporally sensitive claim with no
authorised half-life produces `MISSING_TEMPORAL_PARAMETER` and the evidence
becomes non-scorable. Shipping "30 days" as a placeholder would be worse than
shipping nothing: it would work, nothing would record that it was a guess, and
every downstream score would rest on it (§19).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from sros_contracts import AggregationProfileStatus, ClaimTemporality

from .errors import ProfileError, UncalibratedProfileError
from .items import ITEM_QUALITY_COMPONENTS
from .masses import ALGORITHM_VERSION

__all__ = [
    "LevelThresholds",
    "EvidenceAggregationProfile",
    "REFERENCE_PROFILE_V1",
    "STRUCTURAL_LEVEL_THRESHOLDS",
]


@dataclass(frozen=True)
class LevelThresholds:
    """Structural minimums for EvidenceLevel, not fitted values.

    "Repeated" cannot mean fewer than two independent observations and
    "multi-source" cannot mean one source. Those are definitional, which is why
    V1 can state them without calibration. Whether *three* groups is the right
    bar for Strong Multi-Source is an empirical question, and a calibrated
    profile may raise it — hence parameters rather than constants.
    """

    repeated_signal_min_groups: int = 2
    multi_source_min_groups: int = 3
    multi_source_min_families: int = 2

    def __post_init__(self) -> None:
        if self.repeated_signal_min_groups < 2:
            raise ProfileError(
                "Repeated Signal requires at least 2 independent groups by definition; "
                "a threshold of 1 would make a single record a repetition"
            )
        if self.multi_source_min_groups < self.repeated_signal_min_groups:
            raise ProfileError(
                "Strong Multi-Source cannot require fewer groups than Repeated Signal"
            )
        if self.multi_source_min_families < 2:
            raise ProfileError("Multi-source requires at least 2 source families by definition")

    def to_json(self) -> dict[str, int]:
        return {
            "repeated_signal_min_groups": self.repeated_signal_min_groups,
            "multi_source_min_groups": self.multi_source_min_groups,
            "multi_source_min_families": self.multi_source_min_families,
        }


STRUCTURAL_LEVEL_THRESHOLDS = LevelThresholds()


@dataclass(frozen=True)
class EvidenceAggregationProfile:
    """A named, versioned parameter set with an explicit calibration status."""

    profile_id: str
    version: str
    status: AggregationProfileStatus
    algorithm_version: str = ALGORITHM_VERSION

    applies_to: tuple[str, ...] = ()
    default_temporality: ClaimTemporality = ClaimTemporality.TEMPORALLY_SENSITIVE

    # claim feature -> half-life in days. EMPTY IN V1, on purpose (§19).
    half_life_days: Mapping[str, float] = field(default_factory=dict)

    required_item_fields: tuple[str, ...] = ITEM_QUALITY_COMPONENTS
    level_thresholds: LevelThresholds = STRUCTURAL_LEVEL_THRESHOLDS

    calibration_dataset_ref: str | None = None
    calibrated_at: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version:
            raise ProfileError("a profile needs an id and a version to be referenced later")
        for feature, half_life in self.half_life_days.items():
            if not (half_life > 0):
                raise ProfileError(f"half-life for {feature!r} must be positive, got {half_life!r}")
        if self.status is AggregationProfileStatus.CALIBRATED and not self.calibration_dataset_ref:
            raise ProfileError(
                f"{self.profile_id}: CALIBRATED without a calibration_dataset_ref. A "
                "calibration nobody can re-run is a claim, not a calibration"
            )

    # -- gates ---------------------------------------------------------------

    @property
    def is_calibrated(self) -> bool:
        return self.status is AggregationProfileStatus.CALIBRATED

    def require_runnable(self, *, allow_uncalibrated: bool) -> None:
        """Refuse to run a profile that must not be run.

        DRAFT and RETIRED refuse outright: one is unfinished, the other was
        replaced for a reason. UNCALIBRATED runs only when the caller says so,
        which is the mechanical form of §41 — the framework being defined does
        not make production scoring available.
        """
        if self.status is AggregationProfileStatus.DRAFT:
            raise ProfileError(f"{self.profile_id} is DRAFT and cannot be run")
        if self.status is AggregationProfileStatus.RETIRED:
            raise ProfileError(
                f"{self.profile_id} v{self.version} is RETIRED. It is kept so historical "
                "results stay readable, not so new ones can be produced"
            )
        if self.status is AggregationProfileStatus.UNCALIBRATED and not allow_uncalibrated:
            raise UncalibratedProfileError(
                f"{self.profile_id} v{self.version} is UNCALIBRATED: its parameters were "
                "never fitted to labelled data. Pass allow_uncalibrated=True for "
                "synthetic or experimental work, and label the output as such. "
                "Production research requires a CALIBRATED profile "
                "(evidence-aggregation-framework-v1.md §14)"
            )

    def half_life_for(self, claim_feature: str | None) -> float | None:
        """The authorised half-life, or None. Never a fallback constant."""
        if claim_feature is None:
            return None
        return self.half_life_days.get(claim_feature)

    def to_json(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "status": self.status.value,
            "algorithm_version": self.algorithm_version,
            "applies_to": list(self.applies_to),
            "default_temporality": self.default_temporality.value,
            "half_life_days": dict(self.half_life_days),
            "required_item_fields": list(self.required_item_fields),
            "level_thresholds": self.level_thresholds.to_json(),
            "calibration_dataset_ref": self.calibration_dataset_ref,
            "calibrated_at": self.calibrated_at,
        }


REFERENCE_PROFILE_V1 = EvidenceAggregationProfile(
    profile_id="reference-v1",
    version="1.0.0",
    status=AggregationProfileStatus.UNCALIBRATED,
    applies_to=("*",),
    # Empty. This is the honest state of the system, and the mechanism that
    # makes it visible: any temporally sensitive claim run under this profile
    # reports MISSING_TEMPORAL_PARAMETER instead of quietly using a guess.
    half_life_days=MappingProxyType({}),
    notes=(
        "The V1 reference parameters. Structural only: the level thresholds follow from "
        "what the words mean, and no half-life exists because none has been measured. "
        "Suitable for synthetic sensitivity work and as an implementation oracle. NOT "
        "suitable for production research."
    ),
)
