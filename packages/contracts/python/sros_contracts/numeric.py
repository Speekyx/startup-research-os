"""Validated numeric domain types.

`scoring-framework-v1.1.md` §4.1 defines four distinct quantities. They are not
interchangeable, and the single most likely silent bug in this system is a
confidence rendered on the score scale or vice versa.

Naming rule, enforced here and by lint:
    a field named `confidence` is always [0.0, 1.0]
    a field named `*_score`     is always 0-100
"""

from __future__ import annotations

import math

from .errors import ContractError
from .generated.domain import NUMERIC_BOUNDS

__all__ = [
    "check_numeric",
    "confidence",
    "probability",
    "reliability",
    "independence",
    "score",
    "evidence_level",
]


def check_numeric(type_name: str, value: object, field: str | None = None) -> float | int:
    """Validate `value` against the generated bounds for `type_name`."""
    field = field or type_name
    bounds = NUMERIC_BOUNDS.get(type_name)
    if bounds is None:
        raise ContractError(field, f"unknown numeric type {type_name!r}")

    # bool is a subclass of int in Python. `True` is not a score.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(field, f"expected a number, got {type(value).__name__}")

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        raise ContractError(field, "must be finite")

    number: float | int
    if bounds["integer"]:
        if isinstance(value, float):
            if not value.is_integer():
                raise ContractError(field, f"{type_name} must be an integer, got {value}")
            number = int(value)
        else:
            number = value
    else:
        number = float(value)

    low = float(bounds["min"])  # type: ignore[arg-type]
    high = float(bounds["max"])  # type: ignore[arg-type]
    if number < low or number > high:
        raise ContractError(
            field, f"{type_name} must be within [{bounds['min']}, {bounds['max']}], got {number}"
        )

    return number


def confidence(value: object, field: str = "confidence") -> float:
    return float(check_numeric("Confidence", value, field))


def probability(value: object, field: str = "probability") -> float:
    return float(check_numeric("Probability", value, field))


def reliability(value: object, field: str = "reliability") -> float:
    return float(check_numeric("Reliability", value, field))


def independence(value: object, field: str = "independence") -> float:
    return float(check_numeric("Independence", value, field))


def score(value: object, field: str = "score") -> int:
    return int(check_numeric("Score", value, field))


def evidence_level(value: object, field: str = "evidence_level") -> int:
    return int(check_numeric("EvidenceLevel", value, field))


def confidence_to_percent(value: float) -> int:
    """Presentation helper. 0.82 -> 82. Never the reverse without going through here."""
    return round(confidence(value) * 100)
