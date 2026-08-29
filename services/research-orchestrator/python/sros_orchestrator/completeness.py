"""Research Completeness — the infrastructure representation only.

Mission 0.4 §17. **No formula is defined here, and none may be inferred from
this shape.**

`scoring-framework-v1.1.md` §2 gives Research Completeness a purpose and §7 an
illustrative value, and defines no way to compute it. That is the same gap D-03
records for the Evidence Score, and it is left open for the same reason: the
first implementer to pick a number picks it forever, unfalsifiably, because
nothing records that it was picked.

What this module does enforce is that a completeness value can never be read
without knowing two things:

    basis      MEASURED, ESTIMATED or UNKNOWN
    reasons    why it is not complete

An estimate that reads as a measurement is exactly the false precision
`scoring-framework-v1.1.md` §10 forbids, applied to the one number that is
supposed to tell a user how much to trust everything else.

**The rule with teeth:** a session with blocked capabilities cannot report a
MEASURED completeness, and cannot report 100 at all. You have not measured what
you could not run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

__all__ = ["CompletenessBasis", "CompletenessRecord"]


class CompletenessBasis(StrEnum):
    """How the value was arrived at. NOT NULL in the schema, on purpose."""

    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CompletenessRecord:
    """One completeness observation for a session.

    Scores are on 0-100 (`scoring-framework-v1.1.md` §4.1) and are integers:
    there is no meaningful 82.37 here, and rendering one would claim precision
    the underlying judgment does not have.
    """

    research_session_id: str
    basis: CompletenessBasis
    measured_score: int | None = None
    estimated_score: int | None = None
    incompleteness_reasons: tuple[str, ...] = ()
    blocked_capabilities: tuple[str, ...] = ()
    notes: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("measured_score", "estimated_score"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"{name} must be an integer on 0-100, never a float or a bool")
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be on 0-100, got {value}")

        if self.basis is CompletenessBasis.MEASURED and self.measured_score is None:
            raise ValueError("a MEASURED record must carry measured_score")
        if self.basis is CompletenessBasis.ESTIMATED and self.estimated_score is None:
            raise ValueError("an ESTIMATED record must carry estimated_score")

        if self.blocked_capabilities:
            if self.basis is CompletenessBasis.MEASURED:
                raise ValueError(
                    "a session with blocked capabilities cannot report MEASURED completeness: "
                    f"{sorted(self.blocked_capabilities)} were never executed. Use ESTIMATED "
                    "with a reason, or UNKNOWN."
                )
            if self.value == 100:
                raise ValueError(
                    "completeness cannot be 100 while capabilities were blocked: "
                    f"{sorted(self.blocked_capabilities)}"
                )
            if not self.incompleteness_reasons:
                raise ValueError(
                    "blocked capabilities require at least one stated reason. A gap with "
                    "no explanation is indistinguishable from work nobody noticed was missing."
                )

    @property
    def value(self) -> int | None:
        """The score this record actually carries, whichever basis it used."""
        if self.basis is CompletenessBasis.MEASURED:
            return self.measured_score
        if self.basis is CompletenessBasis.ESTIMATED:
            return self.estimated_score
        return None

    @property
    def claims_complete(self) -> bool:
        return self.value == 100

    # -- constructors --------------------------------------------------------
    #
    # Named constructors rather than a single one with a basis argument: the
    # basis is the thing most likely to be filled in carelessly, and making it
    # part of the call site's name means the caller states it rather than
    # defaults it.

    @classmethod
    def unknown(
        cls,
        research_session_id: str,
        incompleteness_reasons: tuple[str, ...] = (),
        blocked_capabilities: tuple[str, ...] = (),
    ) -> CompletenessRecord:
        """No completeness can be stated.

        This is the correct record for every session planned today: with
        acquisition and scoring blocked, there is no coverage to measure and no
        basis on which to estimate one.
        """
        return cls(
            research_session_id=research_session_id,
            basis=CompletenessBasis.UNKNOWN,
            incompleteness_reasons=incompleteness_reasons,
            blocked_capabilities=blocked_capabilities,
        )

    @classmethod
    def estimated(
        cls,
        research_session_id: str,
        score: int,
        incompleteness_reasons: tuple[str, ...],
        blocked_capabilities: tuple[str, ...] = (),
    ) -> CompletenessRecord:
        """A judged value. The caller owns the judgment and must say why."""
        if not incompleteness_reasons:
            raise ValueError(
                "an estimate must state why it is not a measurement; otherwise it will be "
                "read as one"
            )
        return cls(
            research_session_id=research_session_id,
            basis=CompletenessBasis.ESTIMATED,
            estimated_score=score,
            incompleteness_reasons=incompleteness_reasons,
            blocked_capabilities=blocked_capabilities,
        )

    @classmethod
    def measured(
        cls,
        research_session_id: str,
        score: int,
        incompleteness_reasons: tuple[str, ...] = (),
    ) -> CompletenessRecord:
        """A value derived from what was actually covered.

        Reachable only when nothing was blocked. Today nothing can produce one,
        which is why the constructor exists but has no caller in the system.
        """
        return cls(
            research_session_id=research_session_id,
            basis=CompletenessBasis.MEASURED,
            measured_score=score,
            incompleteness_reasons=incompleteness_reasons,
        )

    def to_json(self) -> dict[str, object]:
        return {
            "research_session_id": self.research_session_id,
            "basis": self.basis.value,
            "measured_score": self.measured_score,
            "estimated_score": self.estimated_score,
            "incompleteness_reasons": list(self.incompleteness_reasons),
            "blocked_capabilities": list(self.blocked_capabilities),
        }
