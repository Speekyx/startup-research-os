"""The four-mass decomposition, and the Evidence Score.

Mission 1.1 §15–§17.

Support and contradiction are aggregated separately and then decomposed, rather
than netted into one number:

    supported_mass    = s * (1 - c)     evidence points one way, little against
    contradicted_mass = c * (1 - s)     evidence points the other way
    conflict_mass     = s * c           strong evidence BOTH ways
    uncertainty_mass  = (1 - s) * (1 - c)   little evidence either way

They sum to 1 exactly, algebraically, not by normalisation.

The decomposition exists because `s - c` cannot distinguish the two states a
research system most needs to tell apart. A claim with no evidence and a claim
with overwhelming evidence on both sides both net to zero. The first needs more
research; the second needs a human, because something in the market is genuinely
contested. Collapsing them destroys precisely the information this system exists
to preserve (`scoring-framework-v1.1.md` §4.1).

**Contradiction is not a penalty.** There is no `score -= 20 if contradicted`
anywhere. Contradiction enters continuously through `c`: a weak contradiction
moves the result a little, a strong one a lot, and several independent ones
accumulate with the same saturation as support. That is what resolves the
contradiction-penalty half of D-03 without anyone choosing a magic number.

    EvidenceScore = 100 * supported_mass

**It is a score, on 0–100, and it is not a probability.** `EvidenceScore = 82`
does not mean the claim is 82% likely to be true. It means the accumulated
evidence sits mostly in the supported mass. A score published without
`support_strength`, `contradiction_strength`, `conflict_mass` and
`uncertainty_mass` beside it is incomplete, and §16 says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import InvalidFactorError

__all__ = ["ALGORITHM_VERSION", "MassDecomposition", "decompose", "evidence_score"]

# The equations, not the parameters. A change here invalidates comparison
# between results; a change to a profile's parameters does not. Two versions
# because the two move independently, and a single version would hide which
# one moved.
ALGORITHM_VERSION = "1.0.0"

# Masses are computed from validated inputs, so any deviation from an exact sum
# of 1 is representation error. This bound is a couple of orders above the
# double-precision floor -- tight enough to catch an algebra mistake, loose
# enough not to fire on rounding.
MASS_SUM_TOLERANCE = 1e-9


@dataclass(frozen=True)
class MassDecomposition:
    """Where the accumulated evidence sits. Not a probability distribution.

    The four values sum to 1 and are non-negative, which makes them look like
    one. They are not: no sampling process generated them and no event has these
    likelihoods. They describe the STATE OF THE EVIDENCE, which is a different
    kind of thing from the state of the world.
    """

    support_strength: float
    contradiction_strength: float
    supported_mass: float
    contradicted_mass: float
    conflict_mass: float
    uncertainty_mass: float

    @property
    def evidence_score(self) -> float:
        return evidence_score(self.supported_mass)

    def sums_to_one(self, tolerance: float = MASS_SUM_TOLERANCE) -> bool:
        total = (
            self.supported_mass
            + self.contradicted_mass
            + self.conflict_mass
            + self.uncertainty_mass
        )
        return abs(total - 1.0) <= tolerance

    def to_json(self) -> dict[str, float]:
        return {
            "support_strength": self.support_strength,
            "contradiction_strength": self.contradiction_strength,
            "supported_mass": self.supported_mass,
            "contradicted_mass": self.contradicted_mass,
            "conflict_mass": self.conflict_mass,
            "uncertainty_mass": self.uncertainty_mass,
        }


def _require_unit(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise InvalidFactorError(f"{name} must be a number, got {value!r}")
    numeric = float(value)
    if numeric != numeric or not (0.0 <= numeric <= 1.0):
        raise InvalidFactorError(f"{name} must be on [0,1], got {numeric!r}")
    return numeric


def decompose(support_strength: float, contradiction_strength: float) -> MassDecomposition:
    """Split accumulated support and contradiction into four masses."""
    s = _require_unit("support_strength", support_strength)
    c = _require_unit("contradiction_strength", contradiction_strength)

    decomposition = MassDecomposition(
        support_strength=s,
        contradiction_strength=c,
        supported_mass=s * (1.0 - c),
        contradicted_mass=c * (1.0 - s),
        conflict_mass=s * c,
        uncertainty_mass=(1.0 - s) * (1.0 - c),
    )

    # An identity, checked anyway. It is the cheapest possible guard against a
    # future edit that "simplifies" one of these four lines, and the failure it
    # catches would otherwise surface as a subtly wrong score nobody questions.
    if not decomposition.sums_to_one():
        raise InvalidFactorError(
            f"mass decomposition does not sum to 1 for s={s!r}, c={c!r}; "
            "this is an algebra error, not an input error"
        )
    return decomposition


def evidence_score(supported_mass: float) -> float:
    """`100 * supported_mass`, on the canonical 0–100 score scale.

    Returned unrounded. `scoring-framework-v1.1.md` §10 forbids false precision
    in PRESENTATION -- `82`, never `82.37` -- and rounding at the source instead
    would make an internal recomputation disagree with a stored result over
    nothing. Round at the edge.
    """
    return 100.0 * _require_unit("supported_mass", supported_mass)
