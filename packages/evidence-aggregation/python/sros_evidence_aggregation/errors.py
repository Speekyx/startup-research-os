"""Failures the aggregation engine raises rather than absorbs.

The distinction that matters here is between a value that is *missing* and a
value that is *wrong*.

A missing value is ordinary. Extraction fails, a timestamp is absent, a
platform does not expose what a reviewer needed. The engine does not raise for
those: the record becomes NON-SCORABLE, the reason is recorded, and aggregation
continues over what remains. Raising would make one gap destroy an otherwise
usable result.

A wrong value is a bug in whatever produced it — a relevance of 1.4, a record
declared KNOWN_DEPENDENT with nothing to depend on. Those raise, because
silently clamping them would let a defective producer keep producing.
"""

from __future__ import annotations

__all__ = [
    "AggregationError",
    "InvalidFactorError",
    "InvalidEvidenceItemError",
    "UncalibratedProfileError",
    "ProfileError",
]


class AggregationError(ValueError):
    """Base for every refusal in this package."""


class InvalidFactorError(AggregationError):
    """A unit-interval factor was outside [0,1], or was not a finite number.

    Not clamped. `scoring-framework-v1.1.md` §4.1 fixes the range of every one
    of these quantities, so a value outside it means the producer is working to
    a different scale — and clamping would hide exactly that.
    """


class InvalidEvidenceItemError(AggregationError):
    """The record contradicts itself.

    Distinct from an incomplete record. "KNOWN_DEPENDENT with no group id"
    asserts a dependency on nothing; "KNOWN_INDEPENDENT with a group id" claims
    independence and membership at once. Neither is a gap that conservative
    handling can cover, because there is no reading of them that is safe.
    """


class ProfileError(AggregationError):
    """The aggregation profile is internally inconsistent."""


class UncalibratedProfileError(AggregationError):
    """A profile that has never been calibrated was used without saying so.

    Mission 1.1 §41. Defining the equations calibrates nothing, and the two are
    separate gates. Running an UNCALIBRATED profile is legitimate for synthetic
    and experimental work; doing it *without acknowledging it* is how a number
    nobody validated ends up in front of a user.

    Pass `allow_uncalibrated=True` to run one deliberately.
    """
