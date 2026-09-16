"""The text surface a finding's evidence span points into.

A span is only checkable against one exact string. Stack Exchange stores a question body as HTML, and a
model shown raw markup would quote markup, while a model shown rendered text would quote text whose
offsets exist nowhere in storage. So the rendering is itself a versioned contract: a pure, deterministic
function of the two stored fields, re-runnable by anyone holding the record, with a digest.

`se-question-text-surface@1.0.0`:

    surface = unescape(title) + "\\n\\n" + render(body)

- Tags are dropped and entities are decoded. Link targets are dropped, the link text is kept.
- A `<pre>` block is kept byte for byte between `[CODE]` and `[/CODE]` lines. Error output usually lives
  there, and it is also where emotional words appear that are not anybody's evaluation.
- A `<blockquote>` is wrapped in `[QUOTE]` and `[/QUOTE]` lines, so text the asker quoted from elsewhere
  is addressable as not the asker's own statement.
- An image becomes `[IMAGE]`. A list item starts with `- `.
- Outside code, runs of blank lines collapse to one and trailing spaces are stripped. Inside code nothing
  is touched.
- Line endings are LF. Offsets are half-open Python string indices, which are Unicode code points.

The surface is never persisted as a canonical record. It is recomputed from the held record whenever a
span is validated.
"""

from __future__ import annotations

import hashlib
import html
from html.parser import HTMLParser

__all__ = [
    "MARKERS",
    "SURFACE_ID",
    "SURFACE_VERSION",
    "marker_regions",
    "render_question_surface",
    "surface_sha256",
]

SURFACE_ID = "se-question-text-surface"
SURFACE_VERSION = "1.0.0"

CODE_OPEN, CODE_CLOSE = "[CODE]", "[/CODE]"
QUOTE_OPEN, QUOTE_CLOSE = "[QUOTE]", "[/QUOTE]"
IMAGE = "[IMAGE]"
MARKERS = (CODE_OPEN, CODE_CLOSE, QUOTE_OPEN, QUOTE_CLOSE, IMAGE)

_BLOCK = {
    "p",
    "div",
    "ul",
    "ol",
    "table",
    "tr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "br",
    "dl",
}


class _Renderer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[tuple[str, str]] = []  # (kind, text) with kind TEXT | CODE | BREAK
        self.pre_depth = 0
        self.code_buffer: list[str] = []

    def _text(self, value: str) -> None:
        self.parts.append(("TEXT", value))

    def _break(self) -> None:
        self.parts.append(("BREAK", "\n"))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.pre_depth:
            if tag == "pre":
                self.pre_depth += 1
            return
        if tag == "pre":
            self.pre_depth = 1
            self.code_buffer = []
        elif tag == "blockquote":
            self._break()
            self._text(QUOTE_OPEN)
            self._break()
        elif tag == "li":
            self._break()
            self._text("- ")
        elif tag == "img":
            self._text(IMAGE)
        elif tag in _BLOCK:
            self._break()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if self.pre_depth:
            if tag == "pre":
                self.pre_depth -= 1
                if self.pre_depth == 0:
                    code = "".join(self.code_buffer).replace("\r\n", "\n").replace("\r", "\n")
                    self.parts.append(("CODE", code))
            return
        if tag == "blockquote":
            self._break()
            self._text(QUOTE_CLOSE)
            self._break()
        elif tag in _BLOCK or tag == "li":
            self._break()

    def handle_data(self, data: str) -> None:
        if self.pre_depth:
            self.code_buffer.append(data)
        else:
            self._text(data)


def _tidy(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    out: list[str] = []
    for line in lines:
        if line == "" and (not out or out[-1] == ""):
            continue
        out.append(line)
    return "\n".join(out).strip("\n")


def _render_body(body: str) -> str:
    parser = _Renderer()
    parser.feed(body)
    parser.close()
    if parser.pre_depth:  # an unclosed <pre> still keeps its bytes
        parser.parts.append(("CODE", "".join(parser.code_buffer)))
    segments: list[str] = []
    prose: list[str] = []

    def flush() -> None:
        tidy = _tidy("".join(prose))
        if tidy:
            segments.append(tidy)
        prose.clear()

    for kind, value in parser.parts:
        if kind == "CODE":
            flush()
            code = value[:-1] if value.endswith("\n") else value
            segments.append(f"{CODE_OPEN}\n{code}\n{CODE_CLOSE}")
        else:
            prose.append(value)
    flush()
    return "\n\n".join(segments)


def render_question_surface(title: str, body: str | None) -> str:
    """The exact string every span of this contract version points into."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("a community question surface needs a non-empty title")
    head = _tidy(html.unescape(title))
    if body is None or not body.strip():
        return head
    return f"{head}\n\n{_render_body(body)}"


def surface_sha256(surface: str) -> str:
    return hashlib.sha256(surface.encode("utf-8")).hexdigest()


def marker_regions(surface: str) -> list[tuple[str, int, int]]:
    """`(kind, start, end)` for every CODE and QUOTE region, marker lines included.

    A line scanner rather than a pattern, because a quote may contain code. Inside a CODE region only a
    `[/CODE]` line closes it, so code that happens to print a marker cannot open a region.
    """
    regions: list[tuple[str, int, int]] = []
    quote_starts: list[int] = []
    code_start: int | None = None
    offset = 0
    for line in surface.split("\n"):
        line_end = offset + len(line)
        if code_start is not None:
            if line == CODE_CLOSE:
                regions.append(("CODE", code_start, line_end))
                code_start = None
        elif line == CODE_OPEN:
            code_start = offset
        elif line == QUOTE_OPEN:
            quote_starts.append(offset)
        elif line == QUOTE_CLOSE and quote_starts:
            regions.append(("QUOTE", quote_starts.pop(), line_end))
        offset = line_end + 1
    return sorted(regions, key=lambda r: (r[1], r[2], r[0]))
