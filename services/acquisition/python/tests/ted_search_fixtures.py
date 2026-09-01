"""Sanitized TED Search API responses. Mission 1.15.7.

**Hand-written, and small on purpose.** Every notice here is shaped like the
Search API's documented response -- the field names come from its OpenAPI
document and the value shapes from the same schema -- and every value is
invented. Nothing was copied out of a real procurement notice, so there is no
question about what these files carry.

**No natural-person field appears anywhere**, not even as a value the collector
would drop. A fixture containing a contact block would be a personal-data
question in a test suite for a mission whose whole point is not asking for one,
and asserting on its absence would require putting it there.

The shapes worth having fixtures for are the ones the collector branches on:
a scalar where the schema says scalar, a one-element array where the schema
says array, a MANY-element array where a notice really has several lots, an
object keyed by language, a missing monetary block, and four malformed
responses.
"""

from __future__ import annotations

import json
from typing import Any

__all__ = [
    "AWARD_NOTICE",
    "CONTRACT_NOTICE",
    "MALFORMED_NOT_JSON",
    "MULTI_LOT_NOTICE",
    "NOTICE_WITHOUT_IDENTITY",
    "NOTICE_WITHOUT_MONEY",
    "response",
    "response_missing_notices",
    "response_notices_not_a_list",
]


# A contract notice: no award yet, so no award date, no winner and no total
# value. The absences are real ones -- a contract notice does not have them --
# and the collector must not turn them into nulls that look like missing data.
CONTRACT_NOTICE: dict[str, Any] = {
    "publication-number": "00123456-2023",
    "notice-identifier": "11111111-2222-3333-4444-555555555555",
    "notice-version": 1,
    "notice-type": "cn-standard",
    "form-type": "competition",
    "publication-date": "2023-03-02Z",
    "classification-cpv": ["72000000"],
    "contract-nature": ["services"],
    "organisation-name-buyer": {"eng": ["Example Public Buyer"], "fra": ["Acheteur Public"]},
    "organisation-country-buyer": ["DEU"],
    "place-of-performance-country-lot": ["DEU"],
    "place-of-performance-subdiv-lot": ["DE300"],
    "estimated-value-lot": [250000.00],
    "estimated-value-cur-lot": ["EUR"],
}


# An award notice: a winner, an award date, a contract date and a total value.
# `total-value` is a scalar and `tender-value` an array in the schema, so both
# shapes are exercised in one notice rather than in two.
AWARD_NOTICE: dict[str, Any] = {
    "publication-number": "00654321-2023",
    "notice-identifier": "66666666-7777-8888-9999-000000000000",
    "notice-version": 2,
    "notice-type": "can-standard",
    "form-type": "result",
    "publication-date": "2023-03-06Z",
    "classification-cpv": ["45000000"],
    "contract-nature": ["works"],
    "organisation-name-buyer": {"eng": ["Example Public Buyer"]},
    "organisation-name-tenderer": {"eng": ["Example Winning Supplier Ltd"]},
    "organisation-country-buyer": ["DEU"],
    "place-of-performance-country-lot": ["DEU"],
    "place-of-performance-subdiv-lot": ["DE300"],
    "winner-selection-status": ["selec-w"],
    "winner-decision-date": ["2023-02-20Z"],
    "contract-conclusion-date": ["2023-02-28Z"],
    "total-value": 1875000.50,
    "total-value-cur": ["EUR"],
    "tender-value": [1875000.50],
    "tender-value-cur": ["EUR"],
}


# Three lots under ONE publication number. The arrays are parallel and their
# LENGTH is the fact: a collector that deduplicated on the notice number, or
# unwrapped an array to its first element, would silently keep one lot of three.
MULTI_LOT_NOTICE: dict[str, Any] = {
    "publication-number": "00777777-2023",
    "notice-identifier": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "notice-version": 1,
    "notice-type": "can-standard",
    "form-type": "result",
    "publication-date": "2023-03-07Z",
    "classification-cpv": ["30000000", "48000000", "72000000"],
    "contract-nature": ["supplies", "supplies", "services"],
    "organisation-name-buyer": {"eng": ["Example Public Buyer"]},
    "organisation-name-tenderer": {
        "eng": ["Supplier One Ltd", "Supplier Two Ltd", "Supplier Three Ltd"]
    },
    "organisation-country-buyer": ["FRA"],
    "place-of-performance-country-lot": ["FRA", "FRA", "BEL"],
    "place-of-performance-subdiv-lot": ["FR101", "FR101", "BE100"],
    "winner-selection-status": ["selec-w", "selec-w", "selec-w"],
    "tender-value": [11000.00, 22000.00, 33000.00],
    "tender-value-cur": ["EUR", "EUR", "SEK"],
    "framework-maximum-value-lot": [500000.00],
    "framework-maximum-value-cur-lot": ["EUR"],
}


# A notice with no monetary block at all. Absent is not zero, and the payload
# must come through without a fabricated amount or a fabricated currency.
NOTICE_WITHOUT_MONEY: dict[str, Any] = {
    "publication-number": "00888888-2023",
    "notice-identifier": "12121212-3434-5656-7878-909090909090",
    "notice-version": 1,
    "notice-type": "cn-standard",
    "form-type": "competition",
    "publication-date": "2023-03-08Z",
    "classification-cpv": ["79000000"],
    "organisation-name-buyer": {"eng": ["Example Public Buyer"]},
    "organisation-country-buyer": ["ITA"],
}


# No publication number: no source-native identity, so no record may be built.
NOTICE_WITHOUT_IDENTITY: dict[str, Any] = {
    "notice-type": "cn-standard",
    "publication-date": "2023-03-09Z",
    "organisation-name-buyer": {"eng": ["Example Public Buyer"]},
}


MALFORMED_NOT_JSON = "<html><body>Service temporarily unavailable</body></html>"


def response(*notices: dict[str, Any], total: int | None = None) -> str:
    """A well-formed search response carrying the given notices."""
    return json.dumps(
        {
            "notices": list(notices),
            "totalNoticeCount": len(notices) if total is None else total,
            "iterationNextToken": None,
            "timedOut": False,
        }
    )


def response_missing_notices() -> str:
    """The contract-drift case: a 200 with no `notices` key at all."""
    return json.dumps({"totalNoticeCount": 4, "timedOut": False})


def response_notices_not_a_list() -> str:
    return json.dumps({"notices": {"publication-number": "00123456-2023"}})
