"""A normalized record as an EXTRACTOR sees it.

`signal-derivation-runtime-v1.md` §2. The model's `ObservationInput` carries no
payload on purpose -- *reading one is how a model starts interpreting* -- and an
extractor obviously must read the value it is subtracting.

So there are two views of the same row and the split is the point:

    NormalizedObservation   what the EXTRACTOR reads: identity, quality, and the
                            canonical payload
    ObservationInput        what the MODEL validates: identity, kind, resolution
                            and quality, and nothing it could interpret

The extractor computes; the model checks identity, lineage, scope and temporal
shape. Neither does the other's job.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from sros_contracts import (
    NormalizationQualityReason,
    NormalizedPeriodType,
    NormalizedRecordQuality,
)
from sros_signal_model import ObservationInput

__all__ = ["NormalizedObservation", "decimal_from"]


def decimal_from(value: object) -> Decimal | None:
    """An exact decimal, or `None`.

    A `float` is refused rather than converted. The normalization layer parses
    source numbers with `parse_float=Decimal` and stores them as decimal TEXT
    precisely so IEEE-754 never touches them; accepting one here would give that
    back at the first subtraction.
    """
    if value is None or isinstance(value, bool | float):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = Decimal(text)
        except InvalidOperation:
            return None
        return None if not parsed.is_finite() else parsed
    return None


@dataclass(frozen=True)
class NormalizedObservation:
    """One canonical observation, with its payload."""

    normalized_record_id: str
    raw_record_id: str
    source_id: str
    observation_key: str
    record_kind_id: str
    quality: NormalizedRecordQuality
    quality_reasons: frozenset[NormalizationQualityReason]
    payload: Mapping[str, object]

    # ---------------------------------------------------------------- payload

    def section(self, name: str) -> Mapping[str, object]:
        """One payload section, or an empty mapping.

        Never a `KeyError`: a lexical observation has no `geography` key AT ALL
        (not a null one), and code that reached for it should get "absent"
        rather than an exception -- absence is the canonical answer.
        """
        value = self.payload.get(name)
        return value if isinstance(value, Mapping) else {}

    def text(self, section: str, field: str) -> str | None:
        value = self.section(section).get(field)
        return value if isinstance(value, str) else None

    @property
    def period_label(self) -> str:
        return self.text("period", "label") or ""

    @property
    def period_type(self) -> NormalizedPeriodType | None:
        raw = self.text("period", "type")
        try:
            return NormalizedPeriodType(raw) if raw else None
        except ValueError:
            return None

    @property
    def period_start(self) -> datetime | None:
        """The canonical start, aware or naive exactly as it was stored.

        Returned verbatim rather than normalised: a naive bound is a wall-clock
        reading under an unestablished timezone, and coercing it here would
        invent the offset the normalizer refused to invent.
        """
        raw = self.text("period", "start")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None

    @property
    def period_end(self) -> datetime | None:
        raw = self.text("period", "end")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None

    @property
    def value(self) -> Decimal | None:
        return decimal_from(self.section("observation").get("value"))

    @property
    def unit(self) -> str | None:
        return self.text("observation", "unit")

    @property
    def unit_state(self) -> str:
        return self.text("observation", "unit_state") or "UNKNOWN"

    @property
    def term_text(self) -> str | None:
        """The source term, verbatim. Never trimmed, never case-folded."""
        return self.text("term", "text")

    @property
    def gram_size(self) -> int | None:
        value = self.section("term").get("gram_size")
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    # ------------------------------------------------------------ model view

    def to_input(self) -> ObservationInput:
        period_type = self.period_type
        if period_type is None:
            raise ValueError(
                f"{self.normalized_record_id} carries no readable canonical period type; "
                "a record that cannot say what shape its period is cannot be placed in a "
                "derivation window"
            )
        return ObservationInput(
            normalized_record_id=self.normalized_record_id,
            raw_record_id=self.raw_record_id,
            source_id=self.source_id,
            observation_key=self.observation_key,
            record_kind_id=self.record_kind_id,
            period_type=period_type,
            period_label=self.period_label,
            quality=self.quality,
            quality_reasons=self.quality_reasons,
        )
