"""What may leave the deployment, as a closed set rather than a promise.

Mission 1.29 §3 and §9. The four source reviews decide **whether** material may
be transmitted; this module decides **what**, and it is the half a review cannot
enforce.

**A governance decision names a representation, and a representation is an
objective property of code.** So the split follows the rule this repository
already uses for conditions: a judgement is confirmed by a person, an objective
property of what a component is configured to emit is verified mechanically. The
reviews say *the derived canonical representation*; this says which keys that is,
and refuses anything else.

**The permitted payload is an allowlist, and an unknown key refuses.** Not a
denylist: a denylist of forbidden fields is a list somebody has to remember to
extend every time a serializer grows a key, and the key that gets forgotten is
the one that leaks. An unrecognised key fails closed.

**What the current payload actually is.** Internal ids, procedure version
strings, source-native subject identifiers, dimension names, this repository's
own bound sentences, an independence sentence, and Claim statements this
repository composed. **No collected record, no API response body, no article
text, no notice payload, no personal data.** That is not a mitigation applied at
transmission time; it is a property the Opportunity packet already has, because
a packet holds references rather than copied truth.

**GDELT is why `PROHIBITED_REPRESENTATIONS` exists.** Its grant runs to datasets
the GDELT Project releases, which are ngram aggregates, and not to the
third-party articles those aggregates were computed from. No article text is held
today, so the bound constrains a future collector rather than the present one --
which is exactly when a scope limit is worth writing down, rather than after
something has been sent.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

__all__ = [
    "TRANSMISSION_REPRESENTATION_VERSION",
    "PERMITTED_PAYLOAD_KEYS",
    "PROHIBITED_REPRESENTATIONS",
    "PERSONAL_DATA_MARKERS",
    "RepresentationViolation",
    "RepresentationBoundError",
    "check_representation",
]

TRANSMISSION_REPRESENTATION_VERSION = "opportunity-transmission-representation@1.0.0"

#: Every top-level key the Opportunity synthesis payload may carry. Closed.
PERMITTED_PAYLOAD_KEYS = frozenset(
    {
        "packet_id",
        "subject",
        "procedures",
        "source_families",
        "dimensions",
        "dimension_bounds",
        "independence",
        "claims",
        "evidence_ids",
    }
)

#: Representations no source decision in this repository authorises, named so a
#: refusal can cite one. Each entry is (marker, why).
PROHIBITED_REPRESENTATIONS: tuple[tuple[str, str], ...] = (
    (
        "article_text",
        "GDELT's grant covers the datasets it RELEASES, which are ngram aggregates. "
        "A third-party news article body reaches publisher rights those terms do not "
        "speak to, and no review here authorises it.",
    ),
    (
        "article_body",
        "As article_text.",
    ),
    (
        "headline",
        "A headline is publisher-authored text, not a GDELT-released measurement.",
    ),
    (
        "notice_payload",
        "The TED notice payload is raw source material. The TED transmission decision "
        "is UNCLEAR in any case, and even were it permitted the reviewed "
        "representation is the derived canonical one.",
    ),
    (
        "raw_record",
        "A collected record is source material preserved verbatim. Nothing in the "
        "Opportunity synthesis path needs it, and the packet does not hold it.",
    ),
    (
        "response_body",
        "An API response body is the source's own bytes, not a canonical fact.",
    ),
    (
        "question_body",
        "Stack Exchange question text is governed by its own Mission 1.23 decision "
        "and by a different processing purpose. It is not part of this payload.",
    ),
)

#: Field-name fragments that would indicate personal data. §9: prefer aggregate,
#: institutional and non-personal representations, and exclude what is not
#: needed. The Opportunity payload needs none of these.
PERSONAL_DATA_MARKERS: tuple[str, ...] = (
    "owner",
    "author",
    "editor",
    "user_name",
    "username",
    "display_name",
    "email",
    "contact",
    "phone",
    "address",
    "ip_address",
    "person",
    "supplier_name",
    "buyer_name",
    "winner_name",
)


@dataclass(frozen=True)
class RepresentationViolation:
    key: str
    reason: str


class RepresentationBoundError(RuntimeError):
    """Raised when a payload carries something no decision authorises."""

    def __init__(self, violations: tuple[RepresentationViolation, ...]) -> None:
        super().__init__(
            "the payload exceeds the permitted transmission representation "
            f"({TRANSMISSION_REPRESENTATION_VERSION}): "
            + "; ".join(f"{v.key}: {v.reason}" for v in violations)
        )
        self.violations = violations


def _walk_keys(value: object, prefix: str = "") -> list[str]:
    """Every key in the payload, at every depth, as dotted paths."""
    found: list[str] = []
    # `Mapping`, not `dict`. The signature accepts any mapping, and a deep scan
    # that recognised only `dict` would return no paths for anything else --
    # which is a check that fails OPEN, the one failure mode this module may not
    # have.
    if isinstance(value, Mapping):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            found.append(path)
            found.extend(_walk_keys(child, path))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_walk_keys(item, prefix))
    return found


def check_representation(payload: Mapping[str, object]) -> tuple[RepresentationViolation, ...]:
    """Every way this payload exceeds the permitted representation.

    Returns all violations rather than the first: a caller told about one field
    strips it and is refused again on the next.
    """
    violations: list[RepresentationViolation] = []

    for key in sorted(payload):
        if key not in PERMITTED_PAYLOAD_KEYS:
            violations.append(
                RepresentationViolation(
                    key,
                    "not in the permitted payload allowlist. An unrecognised key refuses "
                    "rather than passing, because the field nobody remembered to forbid "
                    "is the field that leaks.",
                )
            )

    paths = _walk_keys(payload)
    for path in paths:
        leaf = path.rsplit(".", 1)[-1].lower()
        for marker, reason in PROHIBITED_REPRESENTATIONS:
            if marker in leaf:
                violations.append(RepresentationViolation(path, reason))
        for marker in PERSONAL_DATA_MARKERS:
            if re.search(rf"(^|_){re.escape(marker)}(_|$)", leaf):
                violations.append(
                    RepresentationViolation(
                        path,
                        "looks like personal data. The Opportunity synthesis "
                        "representation is aggregate and institutional, and §9 requires "
                        "excluding what the engine does not need.",
                    )
                )

    return tuple(violations)
