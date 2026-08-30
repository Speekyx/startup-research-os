"""Synthetic WEB-NGRAM files, and a streaming transport that serves them.

Mission 1.9.3 §44. **These are test fixtures, not captured source responses.**
Nothing here was downloaded from GDELT and nothing here is labelled as though it
were: the four-column contract is documented first-party and was observed once in
Mission 1.9.1, so synthetic data for parser edge cases is permitted precisely
because the shape is no longer a guess.

That distinction is the one Mission 1.9.1 refused to blur when it would not
fabricate a `TimelineTone` envelope whose field names nobody had ever seen. A
fixture built against a documented contract tests a parser; a fixture built
against an imagined contract tests the imagination.
"""

from __future__ import annotations

import gzip
import io
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

from sros_acquisition.collection.errors import AcquisitionFailedError, AcquisitionFailure
from sros_acquisition.collection.transport import DownloadLimits, HttpRequest
from sros_contracts import AcquisitionErrorCode

BUCKET = "20260830091500"
OTHER_BUCKET = "20260830093000"


def rows_to_bytes(rows: Sequence[tuple[str, str, str, str]]) -> bytes:
    """Tab-delimited, newline-terminated, no header — the documented shape."""
    return "".join("\t".join(row) + "\n" for row in rows).encode("utf-8")


def gzipped(payload: bytes) -> bytes:
    buffer = io.BytesIO()
    # mtime=0 so the same rows always produce the same bytes; a fixture whose
    # bytes changed every run would make a byte-count assertion flaky.
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as handle:
        handle.write(payload)
    return buffer.getvalue()


UNIGRAM_ROWS: tuple[tuple[str, str, str, str], ...] = (
    (BUCKET, "ALBANIAN", "dhe", "676"),
    (BUCKET, "ALBANIAN", "e", "1142"),
    # Unicode, and a term whose bytes are longer than its characters.
    (BUCKET, "ALBANIAN", "të", "903"),
    (BUCKET, "ENGLISH", "climate", "48210"),
    (BUCKET, "ENGLISH", "climatic", "311"),
    (BUCKET, "ENGLISH", "weather", "9004"),
    (BUCKET, "FRENCH", "climat", "2211"),
    # Zero is a measurement, not an absence.
    (BUCKET, "FRENCH", "grêle", "0"),
    # Larger than a 64-bit float can represent exactly, so a float round-trip
    # would corrupt it and the test would see it.
    (BUCKET, "JAPANESE", "気候", "9007199254740993"),
)

BIGRAM_ROWS: tuple[tuple[str, str, str, str], ...] = (
    (BUCKET, "ALBANIAN", "do të", "104"),
    (BUCKET, "ENGLISH", "climate change", "18422"),
    (BUCKET, "ENGLISH", "climate policy", "902"),
    (BUCKET, "FRENCH", "changement climatique", "1180"),
)


def unigram_file(rows: Sequence[tuple[str, str, str, str]] | None = None) -> bytes:
    return gzipped(rows_to_bytes(list(rows if rows is not None else UNIGRAM_ROWS)))


def bigram_file(rows: Sequence[tuple[str, str, str, str]] | None = None) -> bytes:
    return gzipped(rows_to_bytes(list(rows if rows is not None else BIGRAM_ROWS)))


def revised_unigram_file() -> bytes:
    """The same observations with one COUNT changed — a source revision (§34)."""
    rows = [list(r) for r in UNIGRAM_ROWS]
    rows[3][3] = "48999"  # ENGLISH / climate
    return gzipped(rows_to_bytes([tuple(r) for r in rows]))  # type: ignore[misc]


# ------------------------------------------------------------- malformed files

MALFORMED: dict[str, bytes] = {
    "extra_field": gzipped(
        rows_to_bytes([(BUCKET, "ENGLISH", "climate", "10")])
        + f"{BUCKET}\tENGLISH\tclimate\tchange\t10\n".encode()
    ),
    "missing_field": gzipped(
        rows_to_bytes([(BUCKET, "ENGLISH", "climate", "10")])
        + f"{BUCKET}\tENGLISH\tclimate\n".encode()
    ),
    "non_integer_count": gzipped(rows_to_bytes([(BUCKET, "ENGLISH", "climate", "many")])),
    "negative_count": gzipped(rows_to_bytes([(BUCKET, "ENGLISH", "climate", "-5")])),
    "decimal_count": gzipped(rows_to_bytes([(BUCKET, "ENGLISH", "climate", "10.5")])),
    "bad_date": gzipped(rows_to_bytes([("2026-08-30", "ENGLISH", "climate", "10")])),
    "unaligned_date": gzipped(rows_to_bytes([("20260830091700", "ENGLISH", "climate", "10")])),
    "empty_language": gzipped(rows_to_bytes([(BUCKET, "", "climate", "10")])),
    # Not UTF-8: a lone continuation byte cannot start a sequence.
    "invalid_utf8": gzipped(f"{BUCKET}\tENGLISH\t".encode() + b"\xff\xfe" + b"\t10\n"),
}

#: A term containing the observation-key separator. NOT malformed: news text
#: contains pipes and the live smoke test found one in the first real file.
#: Kept as a fixture so the parser is proved to ACCEPT it.
PIPE_IN_NGRAM = gzipped(rows_to_bytes([(BUCKET, "ENGLISH", "a|b", "10")]))

#: A gzip stream cut short — the trailer never arrives.
TRUNCATED_GZIP = unigram_file()[:-8]
#: Not gzip at all. An HTML error page is the realistic version of this.
NOT_GZIP = b"<html><head><title>404 Not Found</title></head><body>nope</body></html>"
#: Valid gzip framing over nothing.
EMPTY_GZIP = gzipped(b"")
#: One enormous line with no terminator, to exercise the line ceiling.
NO_NEWLINE = gzipped(f"{BUCKET}\tENGLISH\t".encode() + b"x" * 20_000 + b"\t10")


def amplified_gzip(decompressed_bytes: int) -> bytes:
    """Highly compressible content, to exercise the decompression ceiling.

    A few kilobytes on the wire expanding to megabytes is the shape of a zip
    bomb, and the compressed ceiling alone would not catch it.
    """
    line = f"{BUCKET}\tENGLISH\taaaa\t1\n".encode()
    return gzipped(line * (decompressed_bytes // len(line) + 1))


# ------------------------------------------------------------------- transport


@dataclass
class FakeStreamingTransport:
    """Serves fixture bytes in real chunks, and records what was asked for.

    §45: the ceilings must be tested against something that genuinely streams. A
    double that handed the whole body to the parser in one piece would make
    every bound assertion pass without the bound existing.
    """

    files: dict[str, bytes] = field(default_factory=dict)
    #: filename -> number of consecutive failures before the file is served.
    fail_times: dict[str, int] = field(default_factory=dict)
    #: filename -> an explicit failure to raise instead of serving.
    failures: dict[str, AcquisitionFailure] = field(default_factory=dict)
    chunk_size: int = 8
    requests: list[str] = field(default_factory=list)
    hosts: list[frozenset[str]] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)
    closed: int = 0
    #: How much was actually handed over. A ceiling that fires mid-stream leaves
    #: this below the file size, which is the only way to prove it fired early.
    bytes_sent: int = 0
    chunks_sent: int = 0

    def download(
        self,
        base_url: str,
        request: HttpRequest,
        allowed_hosts: frozenset[str],
        limits: DownloadLimits,
    ) -> Iterator[bytes]:
        self.requests.append(request.path)
        self.hosts.append(allowed_hosts)
        self.bases.append(base_url)

        remaining = self.fail_times.get(request.path, 0)
        if remaining:
            self.fail_times[request.path] = remaining - 1
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.NETWORK_TIMEOUT,
                    detail="the download did not complete (fixture timeout)",
                    source_id="",
                    context={"path": request.path},
                )
            )
        explicit = self.failures.get(request.path)
        if explicit is not None:
            raise AcquisitionFailedError(explicit)
        body = self.files.get(request.path)
        if body is None:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR,
                    detail="the source rejected the request deterministically (HTTP 404)",
                    source_id="",
                    context={"status": 404, "path": request.path},
                )
            )
        return self._chunks(body, limits)

    def _chunks(self, body: bytes, limits: DownloadLimits) -> Iterator[bytes]:
        try:
            sent = 0
            for start in range(0, len(body), self.chunk_size):
                chunk = body[start : start + self.chunk_size]
                sent += len(chunk)
                self.bytes_sent += len(chunk)
                self.chunks_sent += 1
                if sent > limits.max_bytes:
                    raise AcquisitionFailedError(
                        AcquisitionFailure(
                            code=AcquisitionErrorCode.INVALID_RESPONSE,
                            detail=(
                                f"the download exceeded {limits.max_bytes} bytes. This is "
                                "our own operational ceiling, not a limit the source "
                                "published"
                            ),
                            source_id="",
                            context={"bytes_read": sent},
                        )
                    )
                yield chunk
        finally:
            self.closed += 1


def transport_with_defaults(**overrides: object) -> FakeStreamingTransport:
    """The two documented files, ready to serve."""
    files = {
        f"{BUCKET}.1gram.txt.gz": unigram_file(),
        f"{BUCKET}.2gram.txt.gz": bigram_file(),
        f"{OTHER_BUCKET}.1gram.txt.gz": unigram_file(),
    }
    transport = FakeStreamingTransport(files=files)
    for name, value in overrides.items():
        setattr(transport, name, value)
    return transport
