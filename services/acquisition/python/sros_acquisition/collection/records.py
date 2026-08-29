"""What a collected observation is, and what identifies it.

Mission 1.5 §17–§25 and §50.

**One RawRecord is one logical source observation**, not one HTTP response. A
page of the World Bank Indicators API carries fifty observations that revise
independently; storing the page would mean a single changed value invalidates
forty-nine unchanged ones, and that nothing downstream could address an
observation without re-parsing the blob.

Three identities are kept apart, and confusing any two of them is the bug this
module exists to prevent:

    observation_key   WHICH observation. Source, resource, geography, period.
                      Never the value, never the retrieval time
    content_hash      WHAT the source said. The canonical payload, which
                      includes the identifying facts AND the value
    record id         which row. Derived from the two above

From that, §23 and §24 fall out without further machinery:

    same key, same hash    the same observation, unchanged. Not a new row --
                           the existing one is re-sighted
    same key, new hash     the source revised it. A new row, linked to the old
                           by the key, and the old one is superseded rather
                           than overwritten
    new key                a different observation

**The retrieval timestamp is deliberately outside the fingerprint** (§25).
Hashing it would make every retrieval a revision, which is the failure mode that
turns an idempotent collector into one that grows a table forever.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ..compliance.attribution import AttributionFacts, render_attribution
from ..compliance.authorization import AcquisitionAuthorizationContext

__all__ = [
    "COLLECTOR_NAMESPACE",
    "CollectedObservation",
    "RawRecordDraft",
    "build_draft",
    "canonical_fingerprint",
    "canonical_json",
    "observation_key",
]

# Deterministic record ids, so a re-run converges on the row that exists rather
# than inserting a parallel copy. Same argument as the registry's row ids.
COLLECTOR_NAMESPACE = uuid.UUID("6f2a1c94-8d3b-5e07-9a41-2b7c6d5e8f30")


def canonical_json(payload: object) -> str:
    """Sorted keys, no incidental whitespace, stable separators.

    A fingerprint that changed when a source reordered its JSON keys would
    report a revision that did not happen.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_fingerprint(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def observation_key(source_id: str, resource_id: str, geography: str, period: str) -> str:
    """The stable identity of an observation.

    Composed rather than hashed: an operator debugging a revision should be able
    to read the key and know which series it is, and a hash would make them look
    it up. The parts are joined with a separator none of them may contain.
    """
    parts = (source_id, resource_id, geography, period)
    for part in parts:
        if not part or "|" in part:
            raise ValueError(
                f"observation key part {part!r} is empty or contains the separator; the "
                "key would be ambiguous and two observations could collide"
            )
    return "|".join(parts)


@dataclass(frozen=True)
class CollectedObservation:
    """One observation as the source stated it, before any interpretation.

    §36: this is a parse, not a normalization. The field names mirror what the
    source returned; nothing here maps a value into the domain vocabulary,
    converts a unit or decides what a number means.
    """

    source_id: str
    resource_id: str
    indicator: str
    geography: str
    geography_name: str | None
    period: str
    value: float | None
    unit: str | None
    obs_status: str | None
    decimals: int | None
    source_last_updated: str | None = None

    @property
    def key(self) -> str:
        return observation_key(self.source_id, self.resource_id, self.geography, self.period)

    @property
    def payload(self) -> dict[str, object]:
        """The canonical payload: what the source said, and what it was about.

        Deliberately excludes the retrieval time, the page it arrived on and the
        request that fetched it. Those are provenance, not content, and putting
        them here would make two identical retrievals look like a revision.

        `source_last_updated` IS included: the source's own statement of when it
        last revised the series is part of what it said.
        """
        return {
            "source_id": self.source_id,
            "resource_id": self.resource_id,
            "indicator": self.indicator,
            "geography": self.geography,
            "geography_name": self.geography_name,
            "period": self.period,
            "value": self.value,
            "unit": self.unit,
            "obs_status": self.obs_status,
            "decimals": self.decimals,
            "source_last_updated": self.source_last_updated,
        }

    @property
    def content_hash(self) -> str:
        return canonical_fingerprint(self.payload)

    @property
    def observed_at(self) -> datetime | None:
        """Event time (`data-principles.md` §9), at the resolution the source gave.

        A World Bank period is a year. This returns the START of that year, and
        the period string survives verbatim in the payload — so nothing infers a
        finer resolution than the source stated, and the convention is
        recoverable rather than lossy. A period this does not recognise returns
        `None` rather than a guess.
        """
        text = self.period.strip()
        if len(text) == 4 and text.isdigit():
            return datetime(int(text), 1, 1, tzinfo=UTC)
        for fmt in ("%Y-%m", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
        return None


@dataclass(frozen=True)
class RawRecordDraft:
    """A row ready to be written, with everything §19 requires already resolved.

    Built by `from_observation` rather than by a repository, so that a collector
    cannot hand persistence a record whose retention it chose or whose
    attribution it composed. Both come from the authorization context.
    """

    record_id: uuid.UUID
    workspace_id: str
    research_session_id: str | None
    source_id: str
    observation_key: str
    content_hash: str
    source_reference: str
    acquisition_method: str
    payload: dict[str, object]
    provenance: dict[str, object]
    review_version: int
    correlation_id: str
    collector_id: str
    collector_version: str
    collected_at: datetime
    observed_at: datetime | None
    expires_at: datetime
    content_language: str | None = None
    payload_ref: str = "inline"
    attribution_text: str = ""

    def to_json(self) -> dict[str, object]:
        return {
            "record_id": str(self.record_id),
            "source_id": self.source_id,
            "observation_key": self.observation_key,
            "content_hash": self.content_hash,
            "collected_at": self.collected_at.isoformat(),
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "expires_at": self.expires_at.isoformat(),
            "collector": f"{self.collector_id}@{self.collector_version}",
        }


def build_draft(
    observation: CollectedObservation,
    context: AcquisitionAuthorizationContext,
    *,
    workspace_id: str,
    research_session_id: str | None,
    correlation_id: str,
    collector_id: str,
    collector_version: str,
    collected_at: datetime,
    page: int,
    request_path: str,
) -> RawRecordDraft:
    """Assemble one row. Retention and attribution come from the CONTEXT.

    §20 and §21 are enforced here by construction rather than by review: there is
    no parameter for an expiry and no parameter for an attribution string, so a
    collector has nothing to pass even if it wanted to. `expires_at` is the
    resolved raw-retention window, and the attribution notice is rendered from
    the obligation the review recorded.

    Rendering the attribution also *fails closed* (§20): a resource whose
    licence the obligation requires, and which the dataset entry does not carry,
    raises rather than producing a record with no credit attached.
    """
    dataset = context.authorized_dataset(observation.resource_id)
    if dataset is None:  # pragma: no cover - the collector authorises first
        raise ValueError(
            f"{observation.resource_id} is not an authorized dataset; a draft must not be "
            "built for a resource the gate did not clear"
        )

    notice = render_attribution(
        context.attribution,
        AttributionFacts(licence_identifier=dataset.licence),
    )

    expires_at = collected_at + _retention_window(context)
    record_id = uuid.uuid5(
        COLLECTOR_NAMESPACE,
        "|".join((workspace_id, observation.key, observation.content_hash)),
    )

    provenance: dict[str, object] = {
        # §19, in the order an analyst reads them.
        "source_id": observation.source_id,
        "access_profile": context.access[0].label if context.access else None,
        "access_method": context.access[0].access_method if context.access else None,
        "review_version": context.review_version,
        "approval_state": context.approval_state.value,
        "resource_id": observation.resource_id,
        "dataset_family": dataset.dataset_family,
        "indicator": observation.indicator,
        "geography": observation.geography,
        "geography_name": observation.geography_name,
        "period": observation.period,
        "licence": dataset.licence,
        "content_origin": dataset.content_origin,
        "licence_basis": dataset.basis,
        "attribution": notice.to_json(),
        "source_last_updated": observation.source_last_updated,
        "request_path": request_path,
        "page": page,
        # The condition snapshot the authorization rested on. Not the whole
        # verification records: their reasons are long, and what a record needs
        # is which conditions were satisfied when it was collected.
        "condition_snapshot": {
            record.condition_key: record.result.value for record in context.verifications
        },
        "authorization_issued_at": context.issued_at.isoformat(),
        "data_minimisation_allowed": list(context.data_minimisation.allowed),
    }

    return RawRecordDraft(
        record_id=record_id,
        workspace_id=workspace_id,
        research_session_id=research_session_id,
        source_id=observation.source_id,
        observation_key=observation.key,
        content_hash=observation.content_hash,
        # A human-readable reference, NOT the provenance. §19 forbids making an
        # analyst infer provenance from a string like this one, which is why
        # everything above exists.
        source_reference=(
            f"{observation.resource_id}/{observation.geography}/{observation.period}"
        ),
        acquisition_method=context.access[0].access_method if context.access else "UNKNOWN",
        payload=observation.payload,
        provenance=provenance,
        review_version=context.review_version,
        correlation_id=correlation_id,
        collector_id=collector_id,
        collector_version=collector_version,
        collected_at=collected_at,
        observed_at=observation.observed_at,
        expires_at=expires_at,
        attribution_text=notice.text,
    )


def _retention_window(context: AcquisitionAuthorizationContext) -> timedelta:
    """The raw-retention window the governance layer resolved.

    Read from the context and nowhere else. `resolve_retention` has already
    taken the stricter of the baseline and any source override, in that
    direction only, so a collector cannot lengthen it and there is no argument
    here through which it could try (§21).
    """
    return timedelta(days=context.retention.raw_days)
