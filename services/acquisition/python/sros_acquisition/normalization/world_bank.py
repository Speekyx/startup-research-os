"""The World Bank Indicators normalizer.

Mission 1.6 §18. The first adapter, and the reference every later one follows.

**Pure, deterministic transformation.** It reads a `RawRecordView` and reviewed
local configuration, and produces a canonical `NumericObservation`. It opens no
socket, fetches no metadata, calls no model and creates no signal, claim,
embedding or score. CI asserts the first three mechanically rather than trusting
this paragraph.

**Everything it cannot establish stays unestablished.** A unit the endpoint does
not publish is `NOT_PUBLISHED`, not inferred from the indicator code. A
geography code with no reviewed entry is `UNKNOWN`, not guessed from its label.
A value the source did not report is `NOT_REPORTED`, and never zero. Each of
those is a state a consumer can branch on, which is strictly more useful than a
plausible number nobody can check.

What it does NOT do: interpret market meaning, extract claims (§44), embed
(§42), cluster or score (§45). It maps one source-native observation into one
canonical observation and stops.
"""

from __future__ import annotations

from datetime import datetime

from sros_contracts import (
    NormalizationErrorCode,
    NormalizationQualityReason,
    NormalizedRecordQuality,
    NormalizedUnitState,
    NormalizedValueState,
)

from ..registry.retention import EffectiveRetention
from .errors import NormalizationFailedError, NormalizationFailure
from .geography import GeographyMap
from .model import (
    NORMALIZATION_SCHEMA_ID,
    NORMALIZATION_SCHEMA_VERSION,
    CanonicalGeography,
    CanonicalPeriod,
    CanonicalValue,
    NormalizedRecordDraft,
    NumericObservation,
    QualityAssessment,
    QualityReason,
    RawRecordView,
    build_normalized,
    decimal_from,
    year_period,
)

__all__ = [
    "WORLD_BANK_NORMALIZER_ID",
    "WORLD_BANK_NORMALIZER_VERSION",
    "WorldBankNumericNormalizer",
]

# §21. Bumped when the PARSE, the canonical mapping or the reviewed inputs it
# reads change -- never when a message is reworded. Recorded on every row, so a
# future change cannot make old records unauditable, and bumping it is the
# mechanism by which output is allowed to differ from what is already stored.
WORLD_BANK_NORMALIZER_ID = "world-bank-indicators-numeric"
WORLD_BANK_NORMALIZER_VERSION = "1.0.0"

_SOURCE_ID = "world-bank"
_COLLECTOR_ID = "world-bank-indicators"
_METRIC_SCHEME = "world-bank-indicator"

# The three authorized series are annual. Every real record uses a four-digit
# year, so that is the only period form this adapter represents (§16). A
# quarterly or monthly code is reported as unsupported rather than approximated:
# inventing an exact date the source did not give is precisely how January 1
# becomes an event time.
_SUPPORTED_PERIOD = "four-digit year"


class WorldBankNumericNormalizer:
    """Maps World Bank indicator observations to canonical numeric observations."""

    normalizer_id = WORLD_BANK_NORMALIZER_ID
    normalizer_version = WORLD_BANK_NORMALIZER_VERSION
    source_id = _SOURCE_ID
    collector_id = _COLLECTOR_ID
    schema_id = NORMALIZATION_SCHEMA_ID
    schema_version = NORMALIZATION_SCHEMA_VERSION

    # §20 and §54. Declared rather than assumed: a collector version this
    # adapter has never seen may have changed the payload shape, and a parse
    # that half-works on an unknown shape is worse than one that stops.
    #
    # BOTH versions are supported, deliberately. 1.0.0 wrote the value as a JSON
    # number (a float, which is the defect Mission 1.6.1 fixed); 1.1.0 writes a
    # canonical decimal string. `decimal_from` reads either exactly, because the
    # repository parses the payload text with `parse_float=Decimal` -- so a
    # 1.0.0 record arrives as a Decimal too, exact with respect to what was
    # stored even though what was stored had already lost information.
    #
    # Dropping 1.0.0 would strand every record collected before the bump. They
    # are still true statements about what the source said when they were
    # written, and §8 forbids rewriting them.
    supported_collector_versions: frozenset[str] = frozenset({"1.0.0", "1.1.0"})

    def __init__(self, geography: GeographyMap, retention: EffectiveRetention) -> None:
        self.geography = geography
        # Governance input, never a normalizer's choice (§10). It arrives
        # resolved -- `resolve_retention` has already taken the stricter of the
        # baseline and any source override, in that direction only -- so there
        # is no argument here through which a longer window could be requested.
        self.retention = retention

    # -------------------------------------------------------------- entry point

    def normalize(
        self, record: RawRecordView, *, correlation_id: str, normalized_at: datetime
    ) -> NormalizedRecordDraft:
        """One raw record into one canonical record.

        Raises only when NO record can be produced. A record that can be
        produced but is incomplete comes back with a quality state and reasons
        (§26): discarding it would make a normalizer defect look like a source
        that returned nothing.
        """
        if record.source_id != self.source_id:
            # Defence in depth. `select_normalizer` refuses this first, and a
            # guard that only exists further up is one a future caller can route
            # around -- the same argument the transport makes for re-checking
            # the host allowlist.
            raise NormalizationFailedError(
                NormalizationFailure(
                    code=NormalizationErrorCode.UNSUPPORTED_SOURCE,
                    detail=(
                        f"this normalizer serves {self.source_id!r} and was handed a record "
                        f"from {record.source_id!r}. One source's shape never describes "
                        "another's"
                    ),
                    source_id=record.source_id,
                    raw_record_id=record.record_id,
                    correlation_id=correlation_id,
                )
            )

        payload = record.payload
        if not payload:
            raise NormalizationFailedError(
                NormalizationFailure(
                    code=NormalizationErrorCode.INVALID_RAW_RECORD,
                    detail=(
                        "the raw record carries no payload, so there is nothing to "
                        "normalize. Never repaired: the raw layer records what the source "
                        "returned"
                    ),
                    source_id=record.source_id,
                    raw_record_id=record.record_id,
                    correlation_id=correlation_id,
                )
            )

        reasons: list[QualityReason] = []
        observation = self._observation(record, payload, reasons)
        assessment = self._assess(reasons)

        return build_normalized(
            record,
            observation,
            assessment,
            self.retention,
            normalizer_id=self.normalizer_id,
            normalizer_version=self.normalizer_version,
            normalized_at=normalized_at,
            correlation_id=correlation_id,
            schema_id=self.schema_id,
            schema_version=self.schema_version,
        )

    # ------------------------------------------------------------------ mapping

    def _observation(
        self,
        record: RawRecordView,
        payload: dict[str, object],
        reasons: list[QualityReason],
    ) -> NumericObservation:
        metric_id = _text(payload.get("indicator"))
        if not metric_id:
            # INVALID rather than a refusal: the record still exists and still
            # has to be findable (§26). But nothing can be said about what the
            # value measures, so it must never be read as an observation.
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.METRIC_MISSING,
                    detail="the raw payload names no indicator, so the value measures nothing",
                    field_path="metric.id",
                )
            )

        period = self._period(payload, reasons)
        geography = self._geography(record, payload, reasons)
        value = self._value(payload, reasons)

        return NumericObservation(
            metric_id=metric_id or "",
            # The Indicators API response carries no indicator label. An
            # absence, recorded faithfully -- deriving one from the code would
            # be exactly the inference §17 and §41 forbid.
            metric_name=None,
            metric_scheme=_METRIC_SCHEME,
            value=value,
            period=period,
            geography=geography,
            dataset=_text(record.provenance.get("dataset_family")),
            resource_id=_text(payload.get("resource_id")),
            # Not read off the period: the three authorized series are annual
            # because the review says so, and the provenance records the family.
            # A source that started returning quarterly data would fail the
            # period check above rather than be relabelled here.
            frequency="ANNUAL",
            source_last_updated=_text(payload.get("source_last_updated")),
        )

    def _period(self, payload: dict[str, object], reasons: list[QualityReason]) -> CanonicalPeriod:
        label = _text(payload.get("period"))
        try:
            return year_period(label or "")
        except ValueError:
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.PERIOD_NOT_SUPPORTED,
                    detail=(
                        f"{label!r} is not a {_SUPPORTED_PERIOD}, which is the only form "
                        "this adapter represents. Reported rather than approximated: an "
                        "exact date the source did not give would be invented"
                    ),
                    field_path="period",
                )
            )
            # A sentinel period so the record can still be stored and audited
            # (§26). It is reachable only alongside PERIOD_NOT_SUPPORTED, which
            # makes the record INVALID, so nothing reads it as a time.
            return year_period("1970")

    def _geography(
        self,
        record: RawRecordView,
        payload: dict[str, object],
        reasons: list[QualityReason],
    ) -> CanonicalGeography:
        source_code = _text(payload.get("geography"))
        source_name = _text(payload.get("geography_name")) or None
        if not source_code:
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.GEOGRAPHY_MISSING,
                    detail="the raw payload names no geography, so the observation is unplaced",
                    field_path="geography.source_code",
                )
            )
            return CanonicalGeography.unclassified("", source_name)

        entry = self.geography.classify(record.source_id, source_code)
        if entry is None:
            # §15. UNKNOWN, never a country. Guessing from the label would be
            # inference; guessing from the three-letter shape would map `WLD` to
            # a country called the world.
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.GEOGRAPHY_NOT_CLASSIFIED,
                    detail=(
                        f"{source_code!r} has no entry in the reviewed geography map, so it "
                        "is established as neither a country nor an aggregate. The source "
                        "code is preserved and no canonical code is assigned"
                    ),
                    field_path="geography.canonical_code",
                )
            )
            return CanonicalGeography.unclassified(source_code, source_name)

        return CanonicalGeography.from_entry(
            entry, source_code, source_name, self.geography.canonical_scheme
        )

    def _value(self, payload: dict[str, object], reasons: list[QualityReason]) -> CanonicalValue:
        unit = _text(payload.get("unit")) or None
        # §17. The Indicators API publishes no unit on this endpoint, so its
        # absence is a settled fact about the access path rather than a gap --
        # which is why it is NOT a quality reason. Marking every record PARTIAL
        # for something every record shares would make the state carry no
        # information.
        unit_state = NormalizedUnitState.PUBLISHED if unit else NormalizedUnitState.NOT_PUBLISHED
        decimals = payload.get("decimals")
        decimal_places = decimals if isinstance(decimals, int) else None

        raw_value = payload.get("value")
        if raw_value is None:
            # §14. The ordinary case for a sparse series, and NEVER zero: zero
            # is a measurement, absence is not, and mapping both to zero would
            # make them permanently indistinguishable.
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.VALUE_NOT_REPORTED,
                    detail=(
                        "the source published no figure for this metric, geography and "
                        "period. A statement by the source, not a failure -- and not zero"
                    ),
                    field_path="observation.value",
                )
            )
            return CanonicalValue(
                value=None,
                state=NormalizedValueState.NOT_REPORTED,
                unit=unit,
                unit_state=unit_state,
                decimals=decimal_places,
            )

        exact = decimal_from(raw_value)
        if exact is None:
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.MALFORMED_NUMERIC_VALUE,
                    detail=(
                        "the source published something in the value position that could "
                        "not be read as an exact decimal. Distinct from a value the source "
                        "never reported"
                    ),
                    field_path="observation.value",
                )
            )
            return CanonicalValue(
                value=None,
                state=NormalizedValueState.UNREADABLE,
                unit=unit,
                unit_state=unit_state,
                decimals=decimal_places,
            )

        return CanonicalValue(
            value=exact,
            state=NormalizedValueState.REPORTED,
            unit=unit,
            unit_state=unit_state,
            decimals=decimal_places,
        )

    # ------------------------------------------------------------------ quality

    @staticmethod
    def _assess(reasons: list[QualityReason]) -> QualityAssessment:
        """Structural completeness, decided by the reasons collected (§25).

        INVALID beats PARTIAL: a record missing a required canonical field is
        not a usable record with a caveat.
        """
        fatal = {
            NormalizationQualityReason.METRIC_MISSING,
            NormalizationQualityReason.GEOGRAPHY_MISSING,
            NormalizationQualityReason.PERIOD_NOT_SUPPORTED,
        }
        if any(reason.code in fatal for reason in reasons):
            state = NormalizedRecordQuality.INVALID
        elif reasons:
            state = NormalizedRecordQuality.PARTIAL
        else:
            state = NormalizedRecordQuality.VALID
        return QualityAssessment(state=state, reasons=tuple(reasons))


def _text(value: object) -> str:
    return str(value).strip() if isinstance(value, str) else ""
