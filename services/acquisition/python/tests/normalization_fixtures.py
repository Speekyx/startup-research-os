"""Fixture builders for the normalization suites.

Shared rather than duplicated, because three suites need the same raw record and
a copy that drifted would make one of them silently test a different shape.

**The provenance here mirrors what the collector actually writes.** It is not a
convenient minimum: a fixture that omitted the attribution would make the §46
test pass for the wrong reason, and one that omitted the condition snapshot
would let a lineage assertion check a field nothing populates in production.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sros_acquisition.normalization import (
    GeographyMap,
    RawRecordView,
    WorldBankNumericNormalizer,
    load_geography_map,
)
from sros_acquisition.registry.retention import EffectiveRetention, resolve_retention

from .conftest import REPO_ROOT, WORKSPACE_P

__all__ = [
    "COLLECTED_AT",
    "NORMALIZED_AT",
    "geography_map",
    "make_normalizer",
    "raw_view",
]

COLLECTED_AT = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
NORMALIZED_AT = datetime(2026, 8, 31, 9, 0, tzinfo=UTC)

_ATTRIBUTION = {
    "text": "The World Bank CC-BY-4.0",
    "elements": [
        {"element": "SOURCE_CREDIT", "text": "The World Bank"},
        {"element": "LICENCE_IDENTIFIER", "text": "CC-BY-4.0"},
    ],
}


def geography_map() -> GeographyMap:
    return load_geography_map(REPO_ROOT / "docs/data/geography-mapping-v1.json")


def make_normalizer(
    geography: GeographyMap | None = None,
    retention: EffectiveRetention | None = None,
) -> WorldBankNumericNormalizer:
    return WorldBankNumericNormalizer(
        geography or geography_map(),
        retention or resolve_retention(None),
    )


def raw_view(
    *,
    record_id: str = "33333333-3333-4333-8333-333333333333",
    workspace_id: str = WORKSPACE_P,
    research_session_id: str | None = None,
    source_id: str = "world-bank",
    indicator: str = "SP.POP.TOTL",
    geography_code: str = "FRA",
    geography_name: str | None = "France",
    period: str = "2018",
    value: object = Decimal("67158348"),
    unit: str | None = None,
    decimals: object = 0,
    collector_id: str = "world-bank-indicators",
    collector_version: str = "1.0.0",
    collected_at: datetime = COLLECTED_AT,
    attribution: dict[str, object] | None = _ATTRIBUTION,
    payload: dict[str, object] | None = None,
    provenance: dict[str, object] | None = None,
) -> RawRecordView:
    """One raw record as the collector would have written it.

    Every override exists because a test needs it, and the defaults are the six
    real observations' shape: `SP.POP.TOTL`, France, an annual period, a
    reported integer value and no published unit.
    """
    body: dict[str, object] = (
        payload
        if payload is not None
        else {
            "source_id": source_id,
            "resource_id": f"indicator/{indicator}",
            "indicator": indicator,
            "geography": geography_code,
            "geography_name": geography_name,
            "period": period,
            "value": value,
            "unit": unit,
            "obs_status": None,
            "decimals": decimals,
            "source_last_updated": "2025-07-01",
        }
    )

    lineage: dict[str, object] = (
        provenance
        if provenance is not None
        else {
            "source_id": source_id,
            "access_profile": "indicators-api-v2",
            "access_method": "PUBLIC_API",
            "review_version": 2,
            "approval_state": "APPROVED_WITH_CONDITIONS",
            "resource_id": f"indicator/{indicator}",
            "dataset_family": "indicators",
            "indicator": indicator,
            "geography": geography_code,
            "geography_name": geography_name,
            "period": period,
            "licence": "CC-BY-4.0",
            "content_origin": "PLATFORM_LICENSED",
            "licence_basis": "Data Catalog default licence for World Bank datasets",
            "source_last_updated": "2025-07-01",
            "request_path": f"country/FR/indicator/{indicator}",
            "page": 1,
            "condition_snapshot": {
                "attribution-required": "SATISFIED",
                "no-microdata": "SATISFIED",
                "indicators-api-only": "SATISFIED",
            },
            "authorization_issued_at": collected_at.isoformat(),
            "data_minimisation_allowed": ["indicator", "geography", "period", "value"],
        }
    )
    if attribution is not None:
        lineage["attribution"] = attribution
    else:
        lineage.pop("attribution", None)

    return RawRecordView(
        record_id=record_id,
        workspace_id=workspace_id,
        research_session_id=research_session_id,
        source_id=source_id,
        observation_key=f"{source_id}|indicator/{indicator}|{geography_code}|{period}",
        content_hash="0" * 64,
        acquisition_method="PUBLIC_API",
        payload=body,
        provenance=lineage,
        review_version=2,
        collector_id=collector_id,
        collector_version=collector_version,
        correlation_id="fixture-correlation",
        collected_at=collected_at,
        observed_at=datetime(int(period) if period.isdigit() else 1970, 1, 1, tzinfo=UTC),
        # 30 days, the resolved raw window. The normalized record deliberately
        # outlives it, which is what the retention tests check.
        expires_at=collected_at + timedelta(days=30),
    )
