"""The two relations, kept apart everywhere.

Mission 1.25 §4.

**`EXACT_ACTIONABLE_EQUIVALENCE` and `SAME_PROBLEM_FAMILY` are different
relations, and neither implies the other in any direction that matters.** They
have different rubrics, different reason codes, different prompts, different
evaluations and different propositions, and a Signal must say which one produced
it. A field that could hold either would eventually hold the wrong one, and the
error would be invisible: both are pairs of question ids with a decision beside
them.

    EXACT_ACTIONABLE_EQUIVALENCE   would the working fix for A tell a reader
                                   what to change for B, in the same component
                                   and the same class of defect?
                                   Mission 1.24. NOT production-ready.

    SAME_PROBLEM_FAMILY            do A and B express substantially the same
                                   user problem, pain or blocked goal, at a
                                   level where one product intervention could
                                   reasonably address both?
                                   Mission 1.25.

**The implications that must never be drawn**, each of which is a sentence
somebody will otherwise write:

    SAME_PROBLEM_FAMILY  =/=>  EXACT_ACTIONABLE_EQUIVALENCE
    SAME_PROBLEM_FAMILY  =/=>  same root cause
    SAME_PROBLEM_FAMILY  =/=>  same fix
    SAME_PROBLEM_FAMILY  =/=>  permission to merge records
    EXACT_ACTIONABLE_EQUIVALENCE  =/=>  a source-native duplicate

The last one is worth its own line. Stack Exchange publishes a duplicate
relation and this repository never acquired it; an equivalence inferred here is
OUR inference and never the site's judgement.

**The looser relation is not a weakened version of the stricter one.** Mission
1.25's brief is explicit: the exact relation stays intact and unweakened, and the
family relation exists because it answers a different question -- an
opportunity-research question rather than a debugging one.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["EquivalenceRelation", "FORBIDDEN_IMPLICATIONS"]


class EquivalenceRelation(StrEnum):
    """Which relation a rubric, classification or Signal is about.

    Required wherever a pairwise judgement is recorded, and never defaulted: a
    default would be chosen once and inherited by every artifact that forgot to
    set it, which is precisely how two relations become one field.
    """

    #: Mission 1.24. The fix for one identifies what to change for the other, in
    #: the same component and the same class of defect. Evaluated and NOT
    #: production-ready.
    EXACT_ACTIONABLE_EQUIVALENCE = "EXACT_ACTIONABLE_EQUIVALENCE"

    #: Mission 1.25. Substantially the same user problem, pain or blocked goal,
    #: at a level where one product intervention could address the family --
    #: even where the technical root causes and fixes differ.
    SAME_PROBLEM_FAMILY = "SAME_PROBLEM_FAMILY"

    def decision_values(self) -> tuple[str, str, str]:
        """(positive, negative, abstain) for this relation.

        Returned rather than imported from the rubric modules, so `evaluate` can
        score either relation without importing both and without a branch per
        relation at every comparison.
        """
        return {
            EquivalenceRelation.EXACT_ACTIONABLE_EQUIVALENCE: (
                "SAME_PROBLEM",
                "DIFFERENT_PROBLEM",
                "ABSTAIN",
            ),
            EquivalenceRelation.SAME_PROBLEM_FAMILY: (
                "SAME_PROBLEM_FAMILY",
                "DIFFERENT_PROBLEM_FAMILY",
                "ABSTAIN",
            ),
        }[self]

    @property
    def proposition_template(self) -> str:
        """What a Signal derived from this relation may say, and no more.

        Held here rather than in the Signal layer, so the sentence and the
        relation cannot drift apart: a proposition written at the point of
        persistence would be written by whoever was persisting.
        """
        return {
            EquivalenceRelation.EXACT_ACTIONABLE_EQUIVALENCE: (
                "Under {procedure}, observations {a} and {b} were classified as describing "
                "the same actionable technical failure concept."
            ),
            EquivalenceRelation.SAME_PROBLEM_FAMILY: (
                "Under {procedure}, observations {a} and {b} were classified as belonging "
                "to the same recurring problem family."
            ),
        }[self]


# Sentences that are false and that a reader will otherwise infer. Kept as data
# so a test can assert none of them appears in a rendered proposition, rather
# than as prose a reviewer has to remember.
FORBIDDEN_IMPLICATIONS: tuple[str, ...] = (
    "the same bug",
    "the same defect",
    "the same root cause",
    "the same fix",
    "duplicate",
    "duplicates",
    "distinct users",
    "different users",
    "how many people",
    "market",
    "demand",
    "willingness to pay",
    "revenue",
)
