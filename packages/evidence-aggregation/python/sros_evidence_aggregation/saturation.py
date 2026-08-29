"""Bounded accumulation across independent groups.

Mission 1.1 §14.

    S = 1 - PRODUCT(1 - g_i)

Chosen for four properties, all of which a plain sum fails:

- **It stays in [0,1].** A sum of five 0.4 groups is 2.0, which is not a
  strength of anything.
- **One strong observation matters.** A single group at 0.9 gives S = 0.9,
  where a mean would dilute it towards the weak members.
- **More independent evidence helps.** S is non-decreasing in every g.
- **Marginal gain falls.** The tenth independent medium group adds far less
  than the first. That is the intended epistemics: after enough independent
  confirmation, another one changes little.

The form is familiar from combining independent probabilities, and the
resemblance is a trap. **S is not a probability.** The g values are contribution
strengths, not likelihoods; nothing here estimates how often the claim turns out
true; and `S = 0.82` licenses no statement about an 82% anything. The operator
was chosen for its shape, not for a probabilistic derivation, and V1 makes no
claim to be modelling one.

Numerically the naive form loses precision when every g is tiny: the product
approaches 1 and `1 - product` cancels. The log form avoids it, and sorting
makes the sum reproducible under input reordering — floating-point addition is
not associative, so §30.7 has to be engineered rather than assumed.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

from .errors import InvalidFactorError

__all__ = ["saturate"]


def saturate(strengths: Iterable[float]) -> float:
    """`1 - prod(1 - g)` over independent group strengths.

    An empty set returns 0.0 — no evidence is no strength, and it is emphatically
    not a strength of zero in the sense of a measured absence. The caller
    distinguishes those two through `aggregation_status`, which reports
    UNAVAILABLE rather than a score of 0.
    """
    values = list(strengths)
    if not values:
        return 0.0

    for value in values:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidFactorError(f"group strength must be a number, got {value!r}")
        numeric = float(value)
        if numeric != numeric or not (0.0 <= numeric <= 1.0):
            raise InvalidFactorError(f"group strength must be on [0,1], got {numeric!r}")

    # A single certain group saturates the operator. Handled before the log form
    # because log1p(-1) is a domain error rather than the -inf the limit wants.
    if any(float(v) >= 1.0 for v in values):
        return 1.0

    # Sorted so the summation order is fixed. Ascending, so the smallest
    # magnitudes are added first and less precision is lost off the end.
    total = 0.0
    for value in sorted(float(v) for v in values):
        total += math.log1p(-value)

    # -expm1(x) == 1 - exp(x), accurate when x is near zero, which is exactly
    # the many-weak-groups case the naive form handles worst.
    result = -math.expm1(total)

    # Clamp for floating-point noise only. The inputs were validated above, so
    # anything outside [0,1] here is representation error of order 1e-16, not a
    # bad input being quietly accepted.
    if result < 0.0:
        return 0.0
    if result > 1.0:
        return 1.0
    return result
