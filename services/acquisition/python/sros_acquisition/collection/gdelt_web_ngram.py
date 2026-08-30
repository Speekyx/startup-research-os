"""The GDELT WEB-NGRAM collector.

Mission 1.9.3. The second collector, and the first for a non-economic source.

It follows the World Bank precedent exactly where the precedent applies, and
differs in the two places the source genuinely differs:

    World Bank        a JSON API, paginated, buffered, one page at a time
    GDELT WEB-NGRAM   a published gzipped file, streamed, four columns, no query

**It cannot run without an authorization.** `collect` takes an
`AcquisitionAuthorizationContext` as its first positional argument, with no
default and no overload that makes one.

**It cannot reach a URL a caller chose.** A `WebNgramRequest` names a resource
kind and exact source bucket labels. There is no field for a host, a path, a
filename or a query, so there is nothing to smuggle one through: the collector
composes `<bucket>.<kind>.txt.gz` from validated parts and the transport refuses
any host outside the allowlist the access profile authorised.

**Two ceilings, and they are different in kind.** `context.authorize_job_size`
is the REVIEWED bound -- eight files per job, decided by GDELT review 3 and not
redefinable here. `NgramBounds` is our own operational safety, chosen for memory
and worker health, and it is labelled `INTERNAL_SAFETY_POLICY` wherever it
appears so nobody later reads it as a quota GDELT published.

**Four fields, and each is preserved rather than interpreted:**

    DATE   the bucket label, verbatim. NO timezone is attached -- GDELT
           documents none, and H-29 is open
    LANG   the CLD2 language NAME, verbatim. Never a geography, never guessed
           into a language tag (H-30)
    NGRAM  the term, verbatim. Not a theme, not an entity, not a topic
    COUNT  an integer GDELT computed over its own corpus. Not a signal, not a
           score, and never through a float

What it does NOT do: normalize, interpret, extract claims, embed or score. It
parses a documented file into observations and stops.
"""

from __future__ import annotations

import zlib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from sros_contracts import AcquisitionErrorCode, ResourceContentOrigin

from ..compliance.authorization import AcquisitionAuthorizationContext
from ..compliance.resources import ResourceDescriptor
from .errors import AcquisitionFailedError, AcquisitionFailure
from .pacing import WEB_NGRAM_PACING, RequestPacer
from .records import (
    RawRecordDraft,
    build_raw_record,
    canonical_fingerprint,
    canonical_number,
    observation_key,
)
from .transport import DownloadLimits, HttpRequest, StreamingTransport, host_of

__all__ = [
    "COLLECTOR_ID",
    "COLLECTOR_VERSION",
    "GRAM_KINDS",
    "GdeltWebNgramCollector",
    "NgramBounds",
    "NgramFileReport",
    "NgramObservation",
    "WebNgramRequest",
    "WebNgramResult",
    "validate_bucket_label",
]

# §3. Bumped when the parse, the identity or the provenance shape changes -- not
# when a message is reworded. Recorded on every row, so a later change cannot
# make existing records unauditable.
COLLECTOR_ID = "gdelt-web-ngram"
COLLECTOR_VERSION = "1.0.0"

_SOURCE_ID = "gdelt"

# The two resources GDELT review 3 authorised, and the only ones this collector
# can name. The mapping is here rather than composed from a caller's string so
# that `3gram` has no spelling that reaches a filename -- §4 refuses it before
# authorization rather than relying on the gate to catch it.
GRAM_KINDS: dict[str, str] = {
    "1gram": "web-ngrams/1gram",
    "2gram": "web-ngrams/2gram",
}

# GDELT publishes on the quarter hour. A label off the grid is a label for a file
# that does not exist, and asking for it would be a request we know will 404.
_ALIGNED_MINUTES = frozenset({0, 15, 30, 45})
_BUCKET_LENGTH = 14


def validate_bucket_label(label: str) -> str:
    """A source bucket label, checked syntactically and returned unchanged.

    §8. **No timezone is attached and none is inferred.** GDELT documents the
    column as `YYYYMMDDHHMMSS` and states no zone anywhere this project could
    find, so parsing it into an aware datetime would put an assumption where a
    fact belongs -- and the assumption would then travel into every record's
    `observed_at`. H-29 is open, and this function is where it would have been
    silently closed.

    What IS checked is structure: fourteen digits, a real calendar date, a
    minute on the published quarter-hour grid, and zero seconds. All four are
    deterministic and none of them requires knowing the zone.
    """
    text = label.strip()
    if len(text) != _BUCKET_LENGTH or not text.isdigit():
        raise ValueError(
            f"bucket label {label!r} must be exactly {_BUCKET_LENGTH} digits in the source's "
            "own YYYYMMDDHHMMSS form"
        )
    year, month, day = int(text[0:4]), int(text[4:6]), int(text[6:8])
    hour, minute, second = int(text[8:10]), int(text[10:12]), int(text[12:14])
    try:
        # Calendar validity only. The result is DISCARDED: constructing it proves
        # 2026-02-30 is not a date, and keeping it would be the timezone
        # assumption arriving through the back door.
        datetime(year, month, day)  # noqa: DTZ001 - deliberate, see above
    except ValueError as exc:
        raise ValueError(f"bucket label {label!r} is not a valid calendar date") from exc
    if not 0 <= hour <= 23:
        raise ValueError(f"bucket label {label!r} has an hour outside 00-23")
    if minute not in _ALIGNED_MINUTES:
        raise ValueError(
            f"bucket label {label!r} is not on the published 15-minute grid "
            f"{sorted(_ALIGNED_MINUTES)}; GDELT publishes no file for it"
        )
    if second != 0:
        raise ValueError(f"bucket label {label!r} must end in 00 seconds")
    return text


@dataclass(frozen=True)
class WebNgramRequest:
    """Intent, not a URL (§7).

    There is no `path`, no `host`, no `filename` and no `query` field. A caller
    says which gram kinds and which source buckets; the collector constructs
    everything else. Adding a free-text field here would reopen the escape the
    whole authorization layer closes.

    The three filter fields are **local** (§22). They decide which parsed rows
    are persisted and change nothing about what a stored observation claims --
    the file still contained every language GDELT monitors, and the request
    provenance records exactly what was filtered so a later reader cannot mistake
    our narrowing for the source's.
    """

    buckets: tuple[str, ...]
    grams: tuple[str, ...] = ("1gram",)
    languages: tuple[str, ...] = ()
    ngrams: tuple[str, ...] = ()
    ngram_prefix: str | None = None

    def __post_init__(self) -> None:
        if not self.buckets:
            raise ValueError("at least one source bucket label is required")
        if not self.grams:
            raise ValueError("at least one gram kind is required")
        unknown = [g for g in self.grams if g not in GRAM_KINDS]
        if unknown:
            raise ValueError(
                f"{unknown} is not a reviewed gram kind. GDELT review 3 assessed "
                f"{sorted(GRAM_KINDS)} and nothing else; a longer ngram is a different "
                "dataset that no review has looked at"
            )
        if len(set(self.grams)) != len(self.grams):
            raise ValueError("a gram kind is requested twice; the same file would be fetched twice")
        object.__setattr__(self, "buckets", tuple(validate_bucket_label(b) for b in self.buckets))
        if len(set(self.buckets)) != len(self.buckets):
            raise ValueError("a bucket is requested twice; the same file would be fetched twice")
        if self.ngram_prefix is not None and not self.ngram_prefix:
            raise ValueError("an empty ngram prefix matches everything; omit it instead")

    @property
    def file_count(self) -> int:
        """What `authorize_job_size` is asked about: one file per bucket per kind."""
        return len(self.buckets) * len(self.grams)

    def resource_id(self, gram: str) -> str:
        return GRAM_KINDS[gram]

    def filename(self, bucket: str, gram: str) -> str:
        """§9. Both parts are validated: the bucket by `validate_bucket_label`
        and the kind by membership in `GRAM_KINDS`. Neither is a caller's
        string by the time it arrives here."""
        return f"{bucket}.{gram}.txt.gz"

    @property
    def filter_json(self) -> dict[str, object]:
        """What was filtered locally, for the record's provenance (§22)."""
        return {
            "languages": list(self.languages),
            "ngrams": list(self.ngrams),
            "ngram_prefix": self.ngram_prefix,
            "applied_by": "collector",
            "note": (
                "Local filtering after parsing. The source file spans every language and "
                "term GDELT monitors; these parameters decided which observed rows were "
                "persisted and changed nothing the source said"
            ),
        }

    def matches(self, language: str, ngram: str) -> bool:
        if self.languages and language not in self.languages:
            return False
        if self.ngrams and ngram not in self.ngrams:
            return False
        return not (self.ngram_prefix is not None and not ngram.startswith(self.ngram_prefix))


@dataclass(frozen=True)
class NgramBounds:
    """INTERNAL_SAFETY_POLICY. **Ours, and not GDELT's** (§12).

    Eight files is the reviewed ceiling and eight files can still hold tens of
    millions of rows: GDELT publishes every language it monitors in one file.
    These are the bounds that keep a worker and a database alive while it reads
    them, and none of them is a limit anybody published.

    They are stated as a dataclass with defaults rather than left to a caller,
    for the reason the World Bank bounds are: "the operator will pass a limit" is
    not a bound, the default is.
    """

    max_compressed_bytes: int = 32 * 1024 * 1024
    max_decompressed_bytes: int = 512 * 1024 * 1024
    max_line_bytes: int = 4096
    max_rows_scanned: int = 20_000_000
    max_records: int = 5_000
    deadline: datetime | None = None

    ORIGIN = "INTERNAL_SAFETY_POLICY"

    def __post_init__(self) -> None:
        for name in (
            "max_compressed_bytes",
            "max_decompressed_bytes",
            "max_line_bytes",
            "max_rows_scanned",
            "max_records",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1; a bound of zero collects nothing")
        if self.max_decompressed_bytes < self.max_compressed_bytes:
            raise ValueError(
                "the decompressed ceiling must not be below the compressed one; gzip does "
                "not make data smaller on the way out"
            )
        if self.deadline is not None and self.deadline.tzinfo is None:
            raise ValueError("deadline must be timezone-aware")

    def to_json(self) -> dict[str, object]:
        return {
            "origin": self.ORIGIN,
            "max_compressed_bytes": self.max_compressed_bytes,
            "max_decompressed_bytes": self.max_decompressed_bytes,
            "max_line_bytes": self.max_line_bytes,
            "max_rows_scanned": self.max_rows_scanned,
            "max_records": self.max_records,
        }


@dataclass(frozen=True)
class NgramObservation:
    """One WEB-NGRAM row, as GDELT published it (§23).

    One RawRecord is one of these -- not one file. A file holds millions of
    independent observations that revise independently, and storing the blob
    would mean nothing downstream could address one without re-parsing it.

    Every field is the source's own value. Nothing here maps a term to a topic,
    a language name to a code, or a count to a strength.
    """

    source_id: str
    resource_id: str
    gram_kind: str
    bucket_label: str
    language_label: str
    ngram: str
    count: int

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError("a WEB-NGRAM count is an occurrence count and cannot be negative")

    @property
    def key(self) -> str:
        """§24. Source-native identity: the source defines every part.

        The resource id is in the key, so a term appearing in both the unigram
        and the bigram file is two observations rather than a collision -- §26
        forbids leaning on the space count in `NGRAM` to tell them apart.

        `count` is deliberately absent: it is content, so a revised count is a
        revision of this observation rather than a different one.
        """
        return observation_key(
            self.source_id,
            self.resource_id,
            self.bucket_label,
            self.language_label,
            self.ngram,
        )

    @property
    def payload(self) -> dict[str, object]:
        """What the source said. §25: no retrieval time, no job id, no filter.

        `count` is a canonical decimal STRING for the reason the World Bank
        value is one: the fingerprint is computed in Python and the payload is
        re-read from `JSONB`, and the two must agree byte for byte about a
        record nobody changed. It never passes through a float.
        """
        return {
            "source_id": self.source_id,
            "resource_id": self.resource_id,
            "gram_kind": self.gram_kind,
            "date": self.bucket_label,
            "lang": self.language_label,
            "ngram": self.ngram,
            "count": canonical_number(Decimal(self.count)),
        }

    @property
    def content_hash(self) -> str:
        return canonical_fingerprint(self.payload)

    @property
    def observed_at(self) -> datetime | None:
        """**`None`, deliberately** (§18).

        `observed_at` is a `TIMESTAMPTZ`, so writing anything here means naming a
        zone. GDELT documents none for this column, so every candidate value
        would be an assumption stored as a fact -- and stored in the column a
        later reader would trust most.

        The bucket label survives verbatim in `payload["date"]` and in
        provenance, so answering H-29 later is a re-derivation over records
        already held rather than a re-collection.
        """
        return None


@dataclass
class NgramFileReport:
    """What one file produced, including what our own bounds stopped (§33)."""

    bucket: str
    gram: str
    resource_id: str
    filename: str
    ok: bool = False
    rows_scanned: int = 0
    rows_matched: int = 0
    compressed_bytes: int = 0
    decompressed_bytes: int = 0
    truncated_by_bound: str | None = None
    content_type: str | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "bucket": self.bucket,
            "gram": self.gram,
            "resource_id": self.resource_id,
            "filename": self.filename,
            "ok": self.ok,
            "rows_scanned": self.rows_scanned,
            "rows_matched": self.rows_matched,
            "compressed_bytes": self.compressed_bytes,
            "decompressed_bytes": self.decompressed_bytes,
            "truncated_by_bound": self.truncated_by_bound,
        }


@dataclass
class WebNgramResult:
    """What one acquisition produced, per file and in total (§33)."""

    source_id: str
    collector_id: str
    collector_version: str
    drafts: list[RawRecordDraft] = field(default_factory=list)
    failures: list[AcquisitionFailure] = field(default_factory=list)
    files: list[NgramFileReport] = field(default_factory=list)
    requests_made: int = 0
    refused_resources: list[str] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return not self.failures

    @property
    def files_requested(self) -> int:
        return len(self.files)

    @property
    def files_processed(self) -> int:
        return sum(1 for f in self.files if f.ok)

    @property
    def files_failed(self) -> int:
        return sum(1 for f in self.files if not f.ok)

    @property
    def rows_scanned(self) -> int:
        return sum(f.rows_scanned for f in self.files)

    @property
    def rows_matched(self) -> int:
        return sum(f.rows_matched for f in self.files)

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "collector": f"{self.collector_id}@{self.collector_version}",
            "records": len(self.drafts),
            "requests_made": self.requests_made,
            "files_requested": self.files_requested,
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "rows_scanned": self.rows_scanned,
            "rows_matched": self.rows_matched,
            "files": [f.to_json() for f in self.files],
            "refused_resources": list(self.refused_resources),
            "failures": [f.to_json() for f in self.failures],
        }


class GdeltWebNgramCollector:
    """Collects GDELT WEB-NGRAM observations, and nothing else."""

    collector_id = COLLECTOR_ID
    collector_version = COLLECTOR_VERSION
    source_id = _SOURCE_ID
    access_profile = "gdelt-web-ngram-files"

    def __init__(
        self,
        transport: StreamingTransport,
        pacer: RequestPacer | None = None,
        now: Callable[[], datetime] | None = None,
        max_attempts: int = 3,
    ) -> None:
        self.transport = transport
        self.pacer = pacer or RequestPacer(WEB_NGRAM_PACING)
        self.now = now or (lambda: datetime.now(UTC))
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.max_attempts = max_attempts

    # ------------------------------------------------------------ the entry point

    def collect(
        self,
        context: AcquisitionAuthorizationContext,
        request: WebNgramRequest,
        *,
        workspace_id: str,
        correlation_id: str,
        research_session_id: str | None = None,
        bounds: NgramBounds | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> WebNgramResult:
        """The only way to collect. The context is the first argument and required.

        The order below is §5's, and it is the order for a reason: **every
        refusal happens before a socket exists.** Job size is checked once for
        the whole request rather than per file, because the reviewed ceiling is
        per job and checking it per file would let a nine-file request through
        as nine one-file successes.
        """
        limits = bounds or NgramBounds()
        result = WebNgramResult(
            source_id=self.source_id,
            collector_id=self.collector_id,
            collector_version=self.collector_version,
        )

        if context.source_id != self.source_id:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        f"this collector serves {self.source_id!r} and was handed an "
                        f"authorization for {context.source_id!r}. One source's approval "
                        "never authorises another's collection"
                    ),
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                )
            )

        # §11. The REVIEWED bound, asked of the context and never redefined here.
        # A request one file over is refused whole: silently splitting it into
        # two permitted jobs would be this collector granting itself a ceiling
        # the review did not.
        size_refusals = context.authorize_job_size(request.file_count)
        if size_refusals:
            result.failures.append(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail="; ".join(size_refusals),
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                    context={"files_requested": request.file_count},
                )
            )
            return result

        base_url, allowed_hosts = self._route(context, correlation_id)

        for gram in request.grams:
            resource_id, refusal = self._authorize(context, gram, correlation_id)
            if refusal is not None:
                # ZERO network calls for a refused resource. The return is before
                # any request is composed, not merely before one is sent.
                result.failures.append(refusal)
                result.refused_resources.append(resource_id)
                continue

            for bucket in request.buckets:
                if self._stop(result, limits, cancelled):
                    return result
                self._collect_file(
                    context=context,
                    request=request,
                    gram=gram,
                    bucket=bucket,
                    resource_id=resource_id,
                    base_url=base_url,
                    allowed_hosts=allowed_hosts,
                    result=result,
                    limits=limits,
                    workspace_id=workspace_id,
                    correlation_id=correlation_id,
                    research_session_id=research_session_id,
                )
        return result

    # ------------------------------------------------------------- authorization

    def _route(
        self, context: AcquisitionAuthorizationContext, correlation_id: str
    ) -> tuple[str, frozenset[str]]:
        """The reviewed base URL and its host. Never a literal, never a fallback.

        **The named profile only** (§10). GDELT carries a second, deferred
        profile for the DOC API; taking `context.access[0]` would work today and
        would silently authorise `api.gdeltproject.org` the day the profile order
        changed. The allowlist is the host of THIS route and nothing else, so
        even the source's own other host is unreachable from here.
        """
        access = next((a for a in context.access if a.label == self.access_profile), None)
        if access is None or not access.endpoint_url:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        f"the authorization carries no {self.access_profile!r} access "
                        "profile with an endpoint, so no host is authorized. An "
                        "unrecorded endpoint is not a licence to guess one"
                    ),
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                )
            )
        host = host_of(access.endpoint_url)
        if not host:
            raise AcquisitionFailedError(  # pragma: no cover - a profile URL always has one
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail="the authorized endpoint has no host",
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                )
            )
        return access.endpoint_url, frozenset({host})

    def _authorize(
        self,
        context: AcquisitionAuthorizationContext,
        gram: str,
        correlation_id: str,
    ) -> tuple[str, AcquisitionFailure | None]:
        """Authorise one resource, before anything opens a socket.

        The descriptor is built from the **authorized dataset entry** and from
        nothing a caller said (§6). The rights basis, the licence (absent under
        a direct grant), the family and the content origin all come from
        governance, so a caller cannot declare its way past the gate and this
        collector cannot invent a licence GDELT does not publish.
        """
        resource_id = GRAM_KINDS[gram]
        dataset = context.authorized_dataset(resource_id)
        if dataset is None:
            return resource_id, AcquisitionFailure(
                code=AcquisitionErrorCode.RESOURCE_NOT_PERMITTED,
                detail=(
                    f"{resource_id} is not an authorized dataset. Its rights basis, family "
                    "and content origin were never recorded, so there is nothing for the "
                    "resource gate to clear it against"
                ),
                source_id=self.source_id,
                correlation_id=correlation_id,
                resource_id=resource_id,
            )

        descriptor = ResourceDescriptor(
            source_id=self.source_id,
            resource_id=resource_id,
            licence=dataset.licence,
            rights_basis=dataset.rights_basis,
            content_origin=ResourceContentOrigin(dataset.content_origin),
            dataset_family=dataset.dataset_family,
            # No geographies. A WEB-NGRAM row has none, and supplying the
            # language here would be the exact confusion §19 forbids.
        )
        authorization = context.authorize_resource(descriptor)
        if not authorization.allowed:
            return resource_id, AcquisitionFailure(
                code=AcquisitionErrorCode.RESOURCE_NOT_PERMITTED,
                detail="; ".join(authorization.denial_reasons),
                source_id=self.source_id,
                correlation_id=correlation_id,
                resource_id=resource_id,
                context={"rules_evaluated": list(authorization.rules_evaluated)},
            )
        return resource_id, None

    # ---------------------------------------------------------------- collection

    def _collect_file(
        self,
        *,
        context: AcquisitionAuthorizationContext,
        request: WebNgramRequest,
        gram: str,
        bucket: str,
        resource_id: str,
        base_url: str,
        allowed_hosts: frozenset[str],
        result: WebNgramResult,
        limits: NgramBounds,
        workspace_id: str,
        correlation_id: str,
        research_session_id: str | None,
    ) -> None:
        """One file: download, decompress, parse, filter, draft.

        **Atomic per file** (§32). Rows accumulate into a local list and reach
        the result only when the file completes. A file that violates the
        documented contract halfway through contributes nothing, because half a
        file is not a smaller success -- it is a file whose provenance would
        claim more than was read.

        Our OWN ceilings are the deliberate exception: hitting `max_records` or
        `max_rows_scanned` stops the scan and **keeps** what was accepted, and
        the report says which bound stopped it. A source-contract violation
        discards; an operational ceiling truncates and says so.
        """
        filename = request.filename(bucket, gram)
        report = NgramFileReport(
            bucket=bucket, gram=gram, resource_id=resource_id, filename=filename
        )
        result.files.append(report)

        http_request = HttpRequest(path=filename)
        download_limits = DownloadLimits(
            max_bytes=limits.max_compressed_bytes,
            # §16. What this client is prepared to read, not a claim about what
            # GDELT sends: Mission 1.9.1 observed `text/plain` for a gzip file,
            # so requiring a MIME type would refuse the real thing.
            accept="*/*",
        )

        collected_at = self.now()
        drafts: list[RawRecordDraft] = []
        remaining = limits.max_records - len(result.drafts)
        try:
            observations = self._read_file(
                base_url=base_url,
                http_request=http_request,
                allowed_hosts=allowed_hosts,
                download_limits=download_limits,
                limits=limits,
                request=request,
                gram=gram,
                resource_id=resource_id,
                report=report,
                remaining=remaining,
                correlation_id=correlation_id,
            )
            for observation in observations:
                drafts.append(
                    build_raw_record(
                        observation,
                        context,
                        workspace_id=workspace_id,
                        research_session_id=research_session_id,
                        correlation_id=correlation_id,
                        collector_id=self.collector_id,
                        collector_version=self.collector_version,
                        collected_at=collected_at,
                        access_label=self.access_profile,
                        source_reference=f"{resource_id}/{bucket}/{observation.language_label}",
                        source_provenance=self._provenance(
                            request=request,
                            observation=observation,
                            filename=filename,
                            report=report,
                            limits=limits,
                        ),
                        # §19. The canonical column stays EMPTY. GDELT emits a
                        # CLD2 language NAME and this project's canonical form is
                        # a language tag; no published mapping between them was
                        # found (H-30), and a name sitting in a column readers
                        # take for a code is the guess this leaves unmade. The
                        # exact label is in the payload, where it is identity.
                        content_language=None,
                    )
                )
        except AcquisitionFailedError as exc:
            result.requests_made = self.pacer.requests_made
            result.failures.append(
                AcquisitionFailure(
                    code=exc.failure.code,
                    detail=exc.failure.detail,
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                    resource_id=resource_id,
                    context={**exc.failure.context, "bucket": bucket, "gram": gram},
                )
            )
            return

        result.requests_made = self.pacer.requests_made
        report.ok = True
        result.drafts.extend(drafts)

    def _provenance(
        self,
        *,
        request: WebNgramRequest,
        observation: NgramObservation,
        filename: str,
        report: NgramFileReport,
        limits: NgramBounds,
    ) -> dict[str, object]:
        """§27, in this source's own vocabulary.

        Everything an analyst needs without parsing a URL: which bucket, which
        gram kind, which language label, which term, which file, what we
        filtered locally, and which of our own ceilings were in force.
        """
        return {
            "gram_kind": observation.gram_kind,
            "source_bucket_label": observation.bucket_label,
            "bucket_resolution_minutes": 15,
            "bucket_timezone": None,
            "bucket_timezone_note": (
                "GDELT documents no timezone for the WEB-NGRAM DATE column, so none is "
                "recorded here. The source label is preserved verbatim (H-29)"
            ),
            "source_language_label": observation.language_label,
            "language_representation": "SOURCE_NATIVE_CLD2_NAME",
            "language_note": (
                "The CLD2 human-readable language name as GDELT emitted it. Not a language "
                "tag, not a geography, and no mapping to either was applied (H-30)"
            ),
            "source_ngram": observation.ngram,
            "received_filename": filename,
            "received_content_type": report.content_type,
            "local_filter": request.filter_json,
            "operational_bounds": limits.to_json(),
            "pacing_origin": WEB_NGRAM_PACING.origin,
        }

    def _stop(
        self,
        result: WebNgramResult,
        limits: NgramBounds,
        cancelled: Callable[[], bool] | None,
    ) -> bool:
        """§38, checked before each file.

        A running HTTP request is not interrupted -- this codebase does not claim
        it can be, and the honest statement is that an in-flight download may
        finish within its own timeout. What IS guaranteed is that no new file
        starts after a cancellation, a deadline or the record ceiling.
        """
        if len(result.drafts) >= limits.max_records:
            return True
        if limits.deadline is not None and self.now() >= limits.deadline:
            result.failures.append(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.CANCELLED,
                    detail="the acquisition deadline passed before the next file",
                    source_id=self.source_id,
                )
            )
            return True
        if cancelled is not None and cancelled():
            result.failures.append(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.CANCELLED,
                    detail="the job was cancelled before the next file",
                    source_id=self.source_id,
                )
            )
            return True
        return False

    # ------------------------------------------------------- download and decode

    def _read_file(
        self,
        *,
        base_url: str,
        http_request: HttpRequest,
        allowed_hosts: frozenset[str],
        download_limits: DownloadLimits,
        limits: NgramBounds,
        request: WebNgramRequest,
        gram: str,
        resource_id: str,
        report: NgramFileReport,
        remaining: int,
        correlation_id: str,
    ) -> list[NgramObservation]:
        """Stream, decompress, parse and filter — then hand back one file's matches.

        **The FILE is streamed; the MATCHES are collected.** The chunks arrive
        bounded, the decompressor is fed one at a time, lines are cut out of a
        small buffer, and a row no filter keeps is discarded immediately. The
        largest thing alive from the file itself is one line, which is what makes
        a twenty-million-row scan possible inside a worker.

        What is retained is the matched subset, bounded by `remaining` and so by
        `max_records`. It is returned as a list rather than yielded, and that is
        a **retry-safety** decision rather than a stylistic one: a failure
        part-way through a stream is retryable, and a generator would already
        have handed its caller the rows read before the failure. The retry then
        re-reads the file from the start and delivers them a second time —
        duplicated observations from one file, produced by the mechanism meant to
        make the fetch reliable. Collecting first means a retried attempt
        discards everything the failed one produced, which is the same per-file
        atomicity `_collect_file` applies one level up.
        """
        last: AcquisitionFailure | None = None
        for attempt in range(1, self.max_attempts + 1):
            self.pacer.acquire()
            chunks: Iterator[bytes] | None = None
            try:
                # Inside the `try`: the real transport is a generator function
                # and raises lazily on the first read, while a test double may
                # raise here. Both have to reach the retry decision, and a call
                # outside would let the eager one escape it entirely.
                chunks = self.transport.download(
                    base_url, http_request, allowed_hosts, download_limits
                )
                return list(
                    self._parse_stream(
                        chunks=chunks,
                        limits=limits,
                        request=request,
                        gram=gram,
                        resource_id=resource_id,
                        report=report,
                        remaining=remaining,
                    )
                )
            except AcquisitionFailedError as exc:
                last = exc.failure
                # §36. Retry a timeout or a 429; never a 404, a malformed file or
                # a refusal. The same request produces the same rejection, and
                # repeating it is how a rate limit becomes a ban.
                if not last.retryable or attempt == self.max_attempts:
                    raise AcquisitionFailedError(
                        AcquisitionFailure(
                            code=last.code,
                            detail=last.detail,
                            source_id=self.source_id,
                            correlation_id=correlation_id,
                            resource_id=resource_id,
                            context={**last.context, "attempts": attempt},
                        )
                    ) from None
                # A retry re-reads the file from the start, so anything this
                # attempt counted has to go with it.
                report.rows_scanned = 0
                report.rows_matched = 0
                report.compressed_bytes = 0
                report.decompressed_bytes = 0
            finally:
                # Release the connection when we stop early -- a cancellation, a
                # ceiling reached, a parse that refused the file. A real
                # generator closes its `with` and returns the socket to the
                # pool; a test double handing back a plain iterator has nothing
                # to close and needs nothing, which is why this asks rather than
                # widening the protocol to demand a method only one
                # implementation has.
                closer = getattr(chunks, "close", None) if chunks is not None else None
                if callable(closer):
                    closer()
        raise AcquisitionFailedError(  # pragma: no cover - the loop returns or raises
            last
            or AcquisitionFailure(
                code=AcquisitionErrorCode.TEMPORARY_UPSTREAM,
                detail="retries exhausted",
                source_id=self.source_id,
                correlation_id=correlation_id,
            )
        )

    def _parse_stream(
        self,
        *,
        chunks: Iterator[bytes],
        limits: NgramBounds,
        request: WebNgramRequest,
        gram: str,
        resource_id: str,
        report: NgramFileReport,
        remaining: int,
    ) -> Iterator[NgramObservation]:
        matched = 0
        for line in self._gzip_lines(chunks, limits, report):
            if not line:
                # A trailing newline is how a text file ends, not a malformed row.
                continue
            report.rows_scanned += 1
            if report.rows_scanned > limits.max_rows_scanned:
                report.truncated_by_bound = "max_rows_scanned"
                return
            language, ngram, count = self._parse_row(line, report)
            if not request.matches(language, ngram):
                continue
            report.rows_matched += 1
            matched += 1
            yield NgramObservation(
                source_id=self.source_id,
                resource_id=resource_id,
                gram_kind=gram,
                bucket_label=self._bucket_of(line),
                language_label=language,
                ngram=ngram,
                count=count,
            )
            if matched >= remaining:
                report.truncated_by_bound = "max_records"
                return

    def _gzip_lines(
        self, chunks: Iterator[bytes], limits: NgramBounds, report: NgramFileReport
    ) -> Iterator[str]:
        """Decompress incrementally and cut lines out of a bounded buffer.

        §14 and §15. `wbits=31` is gzip framing rather than raw deflate, so a
        body that is not gzip fails here rather than producing plausible-looking
        rubbish -- which is what stops an HTML error page from being read as an
        ngram file. A stream that ends before the gzip trailer is a **truncated
        download**, reported as such rather than treated as a short file.

        Three ceilings, all ours: compressed bytes (enforced by the transport),
        decompressed bytes, and the length of one line. The line ceiling matters
        most: without it a file with no newline in it would grow the buffer until
        the worker died, and every other bound would still read as satisfied.
        """
        decompressor = zlib.decompressobj(31)
        buffer = b""
        decompressed = 0

        def fail(code: AcquisitionErrorCode, detail: str) -> AcquisitionFailedError:
            return AcquisitionFailedError(
                AcquisitionFailure(code=code, detail=detail, source_id=self.source_id)
            )

        for chunk in chunks:
            report.compressed_bytes += len(chunk)
            try:
                data = decompressor.decompress(chunk)
            except zlib.error:
                # The library's message is NOT copied: a third party has no
                # obligation to keep anything out of its own error text (§33).
                raise fail(
                    AcquisitionErrorCode.PARSING_FAILURE,
                    "the response is not valid gzip. A WEB-NGRAM resource is published as "
                    "a gzipped file, and a body that does not decompress is not one",
                ) from None
            if not data:
                continue
            decompressed += len(data)
            if decompressed > limits.max_decompressed_bytes:
                raise fail(
                    AcquisitionErrorCode.INVALID_RESPONSE,
                    f"the decompressed file exceeded {limits.max_decompressed_bytes} bytes. "
                    "This is our own operational ceiling, not a limit the source published",
                )
            report.decompressed_bytes = decompressed
            buffer += data
            while True:
                index = buffer.find(b"\n")
                if index < 0:
                    if len(buffer) > limits.max_line_bytes:
                        raise fail(
                            AcquisitionErrorCode.INVALID_RESPONSE,
                            f"a line exceeded {limits.max_line_bytes} bytes with no "
                            "terminator. This is our own operational ceiling",
                        )
                    break
                raw, buffer = buffer[:index], buffer[index + 1 :]
                yield self._decode(raw.rstrip(b"\r"))

        if not decompressor.eof:
            raise fail(
                AcquisitionErrorCode.INVALID_RESPONSE,
                "the gzip stream ended before its trailer; the download is truncated and "
                "the rows already read are not a complete file",
            )
        tail = buffer.rstrip(b"\r\n")
        if tail:
            yield self._decode(tail)

    def _decode(self, raw: bytes) -> str:
        """Strict UTF-8. §20: preserve Unicode deterministically.

        Strict rather than `errors="replace"`: a replacement character would
        become part of an ngram, part of its identity and part of its
        fingerprint, and the corruption would be indistinguishable from a term
        GDELT actually published.
        """
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.PARSING_FAILURE,
                    detail=(
                        "a line is not valid UTF-8. The file is documented as UTF-8 text, "
                        "and substituting replacement characters would put corruption "
                        "inside an ngram's identity"
                    ),
                    source_id=self.source_id,
                )
            ) from None

    # -------------------------------------------------------------------- parsing

    def _parse_row(self, line: str, report: NgramFileReport) -> tuple[str, str, int]:
        """Exactly four tab-separated fields, or the file is refused (§17).

        **No column shifting, no concatenation, no guessing.** A row with a fifth
        field is not a row with a longer ngram: it is a row from a file whose
        contract is not the one this parser was written against, and working
        around it would produce records that look right and are not.

        Fatal for the file rather than skipped, deliberately. The contract is
        documented and observed, so a deviation means the contract changed or
        the file is not what was requested -- and both need a person, which is
        the same stance `world_bank._parse` takes towards an unexpected
        envelope.
        """
        fields = line.split("\t")
        if len(fields) != 4:
            raise self._malformed(
                f"a row has {len(fields)} tab-separated field(s) where the documented "
                "contract has exactly four (DATE, LANG, NGRAM, COUNT)",
                report,
            )
        date_label, language, ngram, count_text = fields
        try:
            validate_bucket_label(date_label)
        except ValueError:
            raise self._malformed(
                "a row's DATE is not a 15-minute bucket label in the documented "
                "YYYYMMDDHHMMSS form",
                report,
            ) from None
        if not language or not ngram:
            raise self._malformed("a row has an empty LANG or NGRAM", report)
        # A term containing `|` is NOT malformed, and an earlier version of this
        # parser refused one. The live smoke test on the first real file found
        # it: news text contains pipes, GDELT publishes terms containing them,
        # and a rule written for identifiers was discarding a whole file of
        # legitimate observations. `observation_key` escapes the separator now
        # (Mission 1.9.3), so there is nothing for this parser to police.
        if not count_text.isdigit():
            # `isdigit` rejects a sign, a decimal point and whitespace in one
            # test. A negative occurrence count is not a small number: it is a
            # field that does not mean what the documentation says it means.
            raise self._malformed(
                "a row's COUNT is not a non-negative integer; GDELT documents it as the "
                "number of times the term was mentioned",
                report,
            )
        # Python's int is arbitrary-precision, so a very large count arrives
        # exact. It never passes through a float (§21).
        return language, ngram, int(count_text)

    def _malformed(self, detail: str, report: NgramFileReport) -> AcquisitionFailedError:
        return AcquisitionFailedError(
            AcquisitionFailure(
                code=AcquisitionErrorCode.INVALID_RESPONSE,
                detail=detail,
                source_id=self.source_id,
                context={"row": report.rows_scanned, "file": report.filename},
            )
        )

    @staticmethod
    def _bucket_of(line: str) -> str:
        """The DATE the row itself carries, not the one we asked for.

        A row states its own bucket and `_parse_row` has already validated it.
        Using the requested label instead would silently relabel a file GDELT
        published under a different stamp, which is a fabricated fact about when
        something was observed.
        """
        return line.split("\t", 1)[0]


def gram_kind_of(resource_id: str) -> str | None:
    """The gram kind behind an authorized resource id, or `None`.

    §26: 1gram and 2gram stay distinguishable by their resource identity, never
    by counting spaces in the term. A two-word entry in the unigram file would
    be a contract violation, and inferring the kind from the text would hide it.
    """
    for kind, resource in GRAM_KINDS.items():
        if resource == resource_id:
            return kind
    return None
