"""What a collected observation is, and what identifies it.

Mission 1.5 §17–§25 and §50.

**One RawRecord is one logical source observation**, not one HTTP response. A
page of the World Bank Indicators API carries fifty observations that revise
independently; storing the page would mean a single changed value invalidates
forty-nine unchanged ones, and that nothing downstream could address an
observation without re-parsing the blob.

Three identities are kept apart, and confusing any two of them is the bug this
module exists to prevent:

    observation_key   WHICH observation. Source, resource, and whatever else
                      the source identifies one by. Never the value, never the
                      retrieval time
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
from decimal import Decimal
from typing import Protocol

from ..compliance.attribution import AttributionFacts, render_attribution
from ..compliance.authorization import AcquisitionAuthorizationContext

__all__ = [
    "COLLECTOR_NAMESPACE",
    "CollectedObservation",
    "RawRecordDraft",
    "SourceObservation",
    "build_draft",
    "build_raw_record",
    "canonical_fingerprint",
    "canonical_json",
    "canonical_number",
    "observation_key",
]

# Deterministic record ids, so a re-run converges on the row that exists rather
# than inserting a parallel copy. Same argument as the registry's row ids.
COLLECTOR_NAMESPACE = uuid.UUID("6f2a1c94-8d3b-5e07-9a41-2b7c6d5e8f30")

#: The one access profile the World Bank review approved. Stated here because
#: `build_draft` is this source's builder; a second profile appearing would make
#: this wrong loudly rather than silently.
WORLD_BANK_ACCESS_PROFILE = "indicators-api-v2"


def canonical_json(payload: object) -> str:
    """Sorted keys, no incidental whitespace, stable separators.

    A fingerprint that changed when a source reordered its JSON keys would
    report a revision that did not happen.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_fingerprint(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def canonical_number(value: Decimal) -> str:
    """The source's number, as a string, exactly as it was sent.

    Mission 1.6.1 §6. Four properties, and each one is load-bearing --
    `raw-numeric-precision-gap-analysis-v1.md` measured what breaks without it:

    **Plain, never scientific.** `json.dumps` writes `1.2345678901234568e+17`
    for a large float and PostgreSQL `JSONB` rewrites that as
    `123456789012345680`. The fingerprint is computed in Python over the first
    and anything re-reading the stored payload sees the second, so the two
    disagree about a record nobody changed.

    **Exact.** The digits the source sent, neither rounded nor padded.

    **Type-preserving.** `1` and `1.0` serialise differently, because the source
    distinguished them. A JSON *number* cannot carry that -- JSON has one numeric
    type -- which is why the value is a string here and at the normalized layer
    (`normalized-record-v1.md` §6.1) for the same reason.

    **Deterministic.** Same input, same bytes, every platform and every run.
    `format(d, "f")` is fixed-point by definition; nothing about it depends on a
    float repr or a locale.
    """
    return format(value, "f")


_KEY_SEPARATOR = "|"
_KEY_ESCAPE = "\\"


def _escape_key_part(part: str) -> str:
    r"""Make one part unambiguous inside a `|`-joined key.

    The escape character is escaped first, or `a\` followed by `b` and `a`
    followed by `\b` would produce the same key.
    """
    return part.replace(_KEY_ESCAPE, _KEY_ESCAPE * 2).replace(
        _KEY_SEPARATOR, _KEY_ESCAPE + _KEY_SEPARATOR
    )


def observation_key(*parts: str) -> str:
    r"""The stable identity of an observation.

    Composed rather than hashed: an operator debugging a revision should be able
    to read the key and know which series it is, and a hash would make them look
    it up.

    **Variadic since Mission 1.9.3, and the arity is the source's business.** A
    World Bank observation is identified by four facts and a GDELT WEB-NGRAM row
    by five -- source, resource, bucket, language, ngram -- so a fixed signature
    would have forced the second to pack two facts into one field.

    **The separator is ESCAPED rather than forbidden, and the live smoke test is
    why.** Until Mission 1.9.3 a part containing `|` was rejected outright, which
    was safe while every part was an identifier, an ISO code or a year. The first
    real WEB-NGRAM file refused to parse: news text contains pipes, so GDELT
    publishes terms containing them, and a rule written for identifiers was
    discarding a whole file of legitimate observations.

    Forbidding was the wrong shape of answer. **Any printable character can
    appear in a term**, so there is no separator to move to; skipping such rows
    would drop real data because of our own key format; and hashing would take
    away the readability the key exists for. Escaping keeps the guarantee --
    distinct part sequences produce distinct keys -- without deciding what a
    source is allowed to say.

    Parts containing neither `|` nor `\` are unaffected, which is every part of
    every record written before this change.
    """
    if len(parts) < 2:
        raise ValueError(
            "an observation key needs at least a source and a resource; fewer parts "
            "would collide across resources of one source"
        )
    for part in parts:
        if not part:
            raise ValueError(
                "an observation key part is empty; the key would be ambiguous and two "
                "observations could collide"
            )
    return _KEY_SEPARATOR.join(_escape_key_part(part) for part in parts)


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
    # A `Decimal`, never a `float` (Mission 1.6.1 §4). The collector parses the
    # response body with `parse_float=Decimal` and `parse_int=Decimal`, so a
    # source value never passes through IEEE-754 on its way here.
    value: Decimal | None
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
            # A canonical decimal STRING, so the value that reaches the
            # fingerprint is the one the source sent. `None` stays JSON null:
            # a value the source did not report is not the string "None", and
            # it is certainly not zero.
            "value": None if self.value is None else canonical_number(self.value),
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


class SourceObservation(Protocol):
    """What every collector's observation must be able to say about itself.

    Mission 1.9.3 §39. Abstracted because TWO collectors now need it and their
    shapes genuinely differ -- a World Bank observation has an indicator, a
    geography and a unit; a WEB-NGRAM row has a language, a term and a count,
    and no geography at all. What they share is exactly this: an identity, a
    canonical payload, a fingerprint over it, and an event time or the honest
    absence of one.

    Everything source-specific -- which provenance facts to record, what a
    human-readable reference looks like -- is supplied by the caller of
    `build_raw_record` rather than guessed here. A protocol that tried to cover
    both field sets would be a union of two vocabularies, which is how a
    "generic bulk source engine" starts.
    """

    @property
    def source_id(self) -> str: ...

    @property
    def resource_id(self) -> str: ...

    @property
    def key(self) -> str: ...

    @property
    def payload(self) -> dict[str, object]: ...

    @property
    def content_hash(self) -> str: ...

    @property
    def observed_at(self) -> datetime | None: ...


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


def build_raw_record(
    observation: SourceObservation,
    context: AcquisitionAuthorizationContext,
    *,
    workspace_id: str,
    research_session_id: str | None,
    correlation_id: str,
    collector_id: str,
    collector_version: str,
    collected_at: datetime,
    access_label: str,
    source_reference: str,
    source_provenance: dict[str, object],
    content_language: str | None = None,
    source_item_link: str | None = None,
) -> RawRecordDraft:
    """Assemble one row. Retention and attribution come from the CONTEXT.

    Mission 1.5 §20 and §21, extracted in Mission 1.9.3 so a second collector
    inherits them rather than reimplementing them. **The properties that matter
    are the ones a collector has no parameter for**: there is no argument for an
    expiry and none for an attribution string, so a collector has nothing to
    pass even if it wanted to.

    `source_provenance` is the collector's own vocabulary -- an indicator and a
    geography for one source, a bucket label and a language label for another.
    It is merged UNDER the governance facts below, so a collector cannot
    overwrite the review version, the rights basis or the condition snapshot by
    choosing a key name.

    Rendering the attribution also *fails closed* (§20, §28): a resource whose
    licence the obligation requires, and which the dataset entry does not carry,
    raises rather than producing a record with no credit attached.

    `access_label` names the route the collector ACTUALLY used, and it is
    required rather than derived. This function used to read `context.access[0]`,
    which was correct while exactly one source had exactly one profile and became
    a lie the moment GDELT carried two: its first profile is the DEFERRED DOC
    API, so every WEB-NGRAM record would have claimed `PUBLIC_API` on
    `api.gdeltproject.org` for a file downloaded over `DATASET_DOWNLOAD` from
    somewhere else. A collector knows which route it took; nothing else does.
    """
    dataset = context.authorized_dataset(observation.resource_id)
    if dataset is None:  # pragma: no cover - the collector authorises first
        raise ValueError(
            f"{observation.resource_id} is not an authorized dataset; a draft must not be "
            "built for a resource the gate did not clear"
        )

    access = next((a for a in context.access if a.label == access_label), None)
    if access is None:
        raise ValueError(
            f"{access_label!r} is not an authorized access profile for "
            f"{observation.source_id}; a record must not name a route the review did not "
            "approve, and it must not name a different one from the one it came over"
        )

    # ADR-031. `source_item_link` is the per-item URL where the licence requires
    # the material itself to be locatable -- CC BY and CC BY-SA both do. Passed
    # by the collector because only the collector knows the canonical link for
    # the thing it just fetched, and left None for a source whose obligation
    # does not include one. A source that DOES declare SOURCE_ITEM_LINK and
    # whose collector passes nothing fails here rather than rendering a partial
    # attribution, which is the behaviour the licence requires.
    notice = render_attribution(
        context.attribution,
        AttributionFacts(
            licence_identifier=dataset.licence,
            source_item_link=source_item_link,
        ),
    )

    expires_at = collected_at + _retention_window(context)
    record_id = uuid.uuid5(
        COLLECTOR_NAMESPACE,
        "|".join((workspace_id, observation.key, observation.content_hash)),
    )

    provenance: dict[str, object] = {
        **source_provenance,
        # §19 and Mission 1.9.3 §27, in the order an analyst reads them. Merged
        # last, so a collector's own keys cannot shadow a governance fact.
        "source_id": observation.source_id,
        "access_profile": access.label,
        "access_method": access.access_method,
        "endpoint": access.endpoint_url,
        "review_version": context.review_version,
        "approval_state": context.approval_state.value,
        "resource_id": observation.resource_id,
        "dataset_family": dataset.dataset_family,
        "licence": dataset.licence,
        # Mission 1.9.3 §27. GDELT's resources are authorised by a DIRECT_GRANT
        # and carry no licence, so a record recording only `licence: null` would
        # be indistinguishable from one whose licence nobody established.
        "rights_basis": dataset.rights_basis.value,
        "content_origin": dataset.content_origin,
        "licence_basis": dataset.basis,
        "attribution": notice.to_json(),
        "retention_days": context.retention.raw_days,
        "retention_basis": context.retention.raw_source,
        "acquisition_bounds": (
            context.acquisition_bounds.to_json() if context.acquisition_bounds else None
        ),
        "condition_snapshot": {
            record.condition_key: record.result.value for record in context.verifications
        },
        "authorization_issued_at": context.issued_at.isoformat(),
        "data_minimisation_allowed": list(context.data_minimisation.allowed),
        # Mission 1.17 found this absent from every RawRecord: provenance
        # recorded the review version and the rights basis but never the PROFILE
        # the job declared, so a record could not say which of two possible
        # answers about its source it was collected under. Added prospectively
        # in Mission 1.18. Historical records are NOT backfilled -- they were
        # written under a model that had no such concept, and inventing the
        # field for them would assert something nobody recorded.
        "use_profile": context.use_profile_id,
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
        source_reference=source_reference,
        acquisition_method=access.access_method,
        payload=observation.payload,
        provenance=provenance,
        review_version=context.review_version,
        correlation_id=correlation_id,
        collector_id=collector_id,
        collector_version=collector_version,
        collected_at=collected_at,
        observed_at=observation.observed_at,
        expires_at=expires_at,
        content_language=content_language,
        attribution_text=notice.text,
    )


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
    """The World Bank record, assembled through the shared core.

    Mission 1.9.3 §39. What is specific to this source is the provenance
    vocabulary below -- an indicator, a geography, a page -- and nothing else.
    The governance half (retention, attribution, identity, the condition
    snapshot) moved to `build_raw_record`, so the second collector inherits it
    rather than reimplementing it and neither can drift from the other.

    **The payload, the key and the fingerprint are untouched by that move.**
    They are computed by the observation, which did not change, so every record
    written before the refactor still hashes to the same value.
    """
    return build_raw_record(
        observation,
        context,
        workspace_id=workspace_id,
        research_session_id=research_session_id,
        correlation_id=correlation_id,
        collector_id=collector_id,
        collector_version=collector_version,
        collected_at=collected_at,
        # Named rather than positional, and named rather than taken from
        # `access[0]`. World Bank has exactly one profile so its behaviour is
        # unchanged; what changed is that the fact is now stated instead of
        # inferred from an ordering nothing guarantees.
        access_label=WORLD_BANK_ACCESS_PROFILE,
        source_reference=(
            f"{observation.resource_id}/{observation.geography}/{observation.period}"
        ),
        source_provenance={
            "indicator": observation.indicator,
            "geography": observation.geography,
            "geography_name": observation.geography_name,
            "period": observation.period,
            "source_last_updated": observation.source_last_updated,
            "request_path": request_path,
            "page": page,
        },
    )


def _retention_window(context: AcquisitionAuthorizationContext) -> timedelta:
    """The raw-retention window the governance layer resolved.

    Read from the context and nowhere else. `resolve_retention` has already
    taken the stricter of the baseline and any source override, in that
    direction only, so a collector cannot lengthen it and there is no argument
    here through which it could try (§21).
    """
    return timedelta(days=context.retention.raw_days)
