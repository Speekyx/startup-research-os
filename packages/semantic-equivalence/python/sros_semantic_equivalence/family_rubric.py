"""The problem-family rubric: three outcomes, one granularity, decided once.

Mission 1.25 §3, and it is a DIFFERENT relation from `rubric.py` rather than a
looser setting of the same one. See `relations.py`.

**The question this rubric asks.** Do two published observations express
substantially the same user problem, pain or blocked goal, at a level where one
product, tool or workflow intervention could reasonably address the family --
even where their technical root causes and their fixes differ?

**The question it does NOT ask**, each written out because each is the reading
somebody will fall into:

    not "is this a duplicate"          the site publishes that; we never acquired it
    not "same root cause"              question text usually cannot establish one
    not "same fix"                     that is `rubric.py`, and it stays intact
    not "same software defect"         a family is about the user, not the code
    not "may these records be merged"  nothing here authorises merging anything

**Why the granularity is set where it is.** Mission 1.24 asked whether the
working fix would transfer, which turned out to need Docker expertise to answer.
This relation is deliberately answerable from the published text by a reader who
knows the product domain and not the fix: *are these two people blocked on
substantially the same thing?* That is the judgement an opportunity researcher
actually makes, and it is the one a reviewer can make honestly.

**And it must not collapse into "both involve Docker".** The corpus is 89 Docker
questions; a relation satisfied by shared technology would return SAME for
everything and mean nothing. The insufficient list below is the load-bearing
half of this rubric, and it is longer than the qualifying rule for that reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .relations import EquivalenceRelation

__all__ = [
    "FAMILY_RUBRIC_VERSION",
    "FAMILY_RELATION",
    "FamilyDecision",
    "FamilyReasonCode",
    "FAMILY_GRANULARITY",
    "FAMILY_INSUFFICIENT_ALONE",
    "FAMILY_WORKED_EXAMPLES",
    "FamilyWorkedExample",
    "FAMILY_RUBRIC_TEXT",
]

FAMILY_RUBRIC_VERSION = "problem-family-rubric@1.0.0"
FAMILY_RELATION = EquivalenceRelation.SAME_PROBLEM_FAMILY


class FamilyDecision(StrEnum):
    """Three outcomes. ABSTAIN is mandatory and is not a degraded DIFFERENT."""

    SAME_PROBLEM_FAMILY = "SAME_PROBLEM_FAMILY"
    DIFFERENT_PROBLEM_FAMILY = "DIFFERENT_PROBLEM_FAMILY"
    ABSTAIN = "ABSTAIN"


class FamilyReasonCode(StrEnum):
    """Why the decision came out that way.

    Written against the shapes the Mission 1.20 Docker corpus actually contains,
    with the observation that motivated each named in its comment. Free text is
    required alongside a code and is never the only audit surface: prose cannot
    be counted or compared across a run.
    """

    #: The qualifying code. Both observations describe being blocked on the same
    #: kind of thing, and one intervention could plausibly help both.
    SHARED_BLOCKED_GOAL = "SHARED_BLOCKED_GOAL"

    #: 78089171 (a Next.js variable undefined in a pod) with 78098380 (Compose
    #: `env_file` absent during the build). Different frameworks, different
    #: components, and the same user problem: a value needed at one phase is
    #: supplied at another. The canonical qualifying shape.
    SHARED_CONFIGURATION_LIFECYCLE_CONFUSION = "SHARED_CONFIGURATION_LIFECYCLE_CONFUSION"

    #: The runc trio, and every pair like it. A shared wrapper, a shared error
    #: class or a shared exit code says what the machine printed, not what the
    #: person was trying to do.
    SHARED_SYMPTOM_ONLY = "SHARED_SYMPTOM_ONLY"

    #: 78096175 (postgres volume does not persist) with a MongoDB connectivity
    #: question. Both are databases in containers; the blocked goals are storage
    #: durability and reachability, which no single intervention addresses.
    SAME_TECHNOLOGY_DIFFERENT_GOAL = "SAME_TECHNOLOGY_DIFFERENT_GOAL"

    #: One or both observations do not establish what the person was trying to
    #: do, so no family can be assigned to them.
    GOAL_NOT_ESTABLISHED = "GOAL_NOT_ESTABLISHED"


FAMILY_GRANULARITY = """\
Two published observations belong to the SAME PROBLEM FAMILY when they describe
substantially the same user problem, pain or blocked goal -- at a level where one
product, tool, documentation change or workflow could reasonably help both people
-- even if the technical root causes differ and even if the fixes differ.

Ask: WHAT WAS EACH PERSON TRYING TO DO, AND WHAT STOPPED THEM? If the answers are
substantially the same thing, it is one family. If one intervention would have to
be two unrelated interventions to help both, it is not.

This is a question about the published descriptions, not about the underlying
truth, and not about the code. Where the text does not establish what the person
was trying to do, the answer is ABSTAIN.\
"""

# The load-bearing half. Every item here is a real property of pairs this corpus
# produces, and each is insufficient BY CONSTRUCTION rather than below some
# threshold -- a threshold would invite "how much shared symptom is enough", and
# the answer is that no amount is.
FAMILY_INSUFFICIENT_ALONE: tuple[str, ...] = (
    "the same tool, runtime or platform. Every observation here is a Docker "
    "question, so a relation satisfied by that would return SAME for everything",
    "the same site tags, however specific",
    "the same language, framework or base image",
    "the same wrapper or harness diagnostic, however long the shared string. "
    "Mission 1.20's three questions share 106 characters of exact runc output and "
    "are three unrelated blocked goals",
    "the same generic error class -- permission denied, connection refused, exit "
    "code 1, HTTP 500, a bare ValueError, 'the build failed'",
    "the same broad category of component. Two database connectivity failures are "
    "not one family merely because both involve databases; MongoDB unreachable "
    "from a container and SQL Server refusing an integrated-security login are "
    "different blocked goals with different interventions",
    "the same lifecycle phase alone. 'Both happen at build time' is a coordinate, not a goal",
)


@dataclass(frozen=True)
class FamilyWorkedExample:
    """One decided pair, with the reasoning that decides it.

    `real` marks whether the pair exists in the Mission 1.20 corpus. The
    qualifying example IS real, which the exact-equivalence rubric could not
    manage -- and that difference is itself a finding about the two relations.
    """

    kind: str
    decision: FamilyDecision
    reason: FamilyReasonCode
    a: str
    b: str
    why: str
    real: bool


FAMILY_WORKED_EXAMPLES: tuple[FamilyWorkedExample, ...] = (
    FamilyWorkedExample(
        kind="qualifying",
        decision=FamilyDecision.SAME_PROBLEM_FAMILY,
        reason=FamilyReasonCode.SHARED_CONFIGURATION_LIFECYCLE_CONFUSION,
        a="78089171 -- a Next.js `NEXT_PUBLIC_` variable is undefined in a Kubernetes "
        "pod even though the environment is set on the pod",
        b="78098380 -- `docker-compose`'s `env_file` supplies variables at container "
        "runtime, and they are absent during the Dockerfile build",
        why=(
            "A REAL CORPUS PAIR, and the one Mission 1.24 classified DIFFERENT under the "
            "exact relation. Both readings were defensible there, because the components "
            "genuinely differ: Next.js build inlining versus Compose build arguments. "
            "Under THIS relation the answer is clear. Each person is trying to get a "
            "configuration value into a place that reads it, and each is defeated by the "
            "same thing -- the value is supplied at one lifecycle phase and needed at "
            "another. One piece of documentation, one linting rule or one tool that "
            "reported 'this variable is read at build time and set at run time' would "
            "help both. That is what a family is"
        ),
        real=True,
    ),
    FamilyWorkedExample(
        kind="non-qualifying",
        decision=FamilyDecision.DIFFERENT_PROBLEM_FAMILY,
        reason=FamilyReasonCode.SHARED_SYMPTOM_ONLY,
        a='78086542 -- OCI runtime create failed ... exec: "/usr/src/app/entrypoint.sh": '
        "permission denied",
        b='78099680 -- OCI runtime create failed ... exec: "gunicorn": executable file '
        "not found in $PATH",
        why=(
            "The Mission 1.20 hard negative, and it must fail HERE TOO. 106 characters of "
            "identical daemon output, and two different blocked goals: getting a script "
            "the image contains to be executable, versus getting a binary into the image "
            "at all. The shared string is what the daemon prints when anything goes wrong "
            "at that step, so it describes the machine's reporting rather than either "
            "person's problem. A wrapper is never a family"
        ),
        real=True,
    ),
    FamilyWorkedExample(
        kind="non-qualifying",
        decision=FamilyDecision.DIFFERENT_PROBLEM_FAMILY,
        reason=FamilyReasonCode.SAME_TECHNOLOGY_DIFFERENT_GOAL,
        a="a container cannot reach a MongoDB instance on the compose network",
        b="a Spring Boot container is refused by SQL Server under integrated security",
        why=(
            "ILLUSTRATION of the trap the brief names. Both are databases, both are in "
            "containers, both emit a connection failure. The blocked goals are network "
            "reachability between compose services and Windows authentication against a "
            "database engine, and no single intervention addresses both. 'Both involve "
            "databases' is a category, not a family"
        ),
        real=False,
    ),
    FamilyWorkedExample(
        kind="borderline",
        decision=FamilyDecision.DIFFERENT_PROBLEM_FAMILY,
        reason=FamilyReasonCode.SHARED_SYMPTOM_ONLY,
        a="78093369 -- installing psycopg in an alpine image fails because the build "
        "toolchain is absent",
        b="78105004 -- a rails image fails because apt-get cannot install libc-bin",
        why=(
            "BORDERLINE, AND DECIDED. Both are 'my Docker build fails while installing a "
            "dependency', both end in `exit code: 1`, and the temptation is to call that a "
            "family: a tool that explained failed package installs would help both. That "
            "is too broad to be useful -- it would make every failed build one family, and "
            "an opportunity built on it would be 'make builds work'. The blocked goals are "
            "getting a Python extension to compile on musl, and getting an apt dependency "
            "resolved on a specific base image. This is where the granularity does its "
            "work: a family must be narrow enough that ONE intervention is describable"
        ),
        real=True,
    ),
    FamilyWorkedExample(
        kind="abstention",
        decision=FamilyDecision.ABSTAIN,
        reason=FamilyReasonCode.GOAL_NOT_ESTABLISHED,
        a="78097071 -- how to set up a database through an npm package in a Docker "
        "container, reporting no failure at all",
        b="78096175 -- a postgres volume whose data does not survive a re-run",
        why=(
            "One side describes no blockage, so there is nothing to compare a blocked goal "
            "against. ABSTAIN rather than DIFFERENT: saying DIFFERENT asserts that the two "
            "goals are distinct, when one of them was never established"
        ),
        real=True,
    ),
)


def _render() -> str:
    """The rubric as the classifier and the reviewer both receive it.

    Rendered from the same constants the code and the tests use, so the text a
    model reads and the text a person reads cannot drift from each other or from
    the definition. A prompt with its own copy of the rules is a second rubric.
    """
    lines = [
        f"RELATION: {FAMILY_RELATION.value}",
        "",
        "This is NOT the exact-equivalence relation. It does not ask whether the fix",
        "for one would fix the other, and a SAME answer here never implies that.",
        "",
        "GRANULARITY -- fixed for every pair, never chosen per pair:",
        "",
        FAMILY_GRANULARITY,
        "",
        "OUTCOMES -- exactly three:",
        "",
        "  SAME_PROBLEM_FAMILY       substantially the same user problem or blocked goal",
        "  DIFFERENT_PROBLEM_FAMILY  different blocked goals",
        "  ABSTAIN                   the text does not establish what one or both were",
        "                            trying to do",
        "",
        "ABSTAIN is a correct answer, not a failure to answer. A wrong",
        "SAME_PROBLEM_FAMILY is the most costly error in this task.",
        "",
        "INSUFFICIENT ALONE -- none of the following makes two observations one family,",
        "on its own or in combination with others from this list:",
        "",
    ]
    lines += [f"  - {item}" for item in FAMILY_INSUFFICIENT_ALONE]
    lines += ["", "REASON CODES -- exactly one per decision:", ""]
    lines += [
        "  SHARED_BLOCKED_GOAL                       the same kind of blockage, one",
        "                                            intervention could help both",
        "  SHARED_CONFIGURATION_LIFECYCLE_CONFUSION  a value is supplied at one phase",
        "                                            and needed at another",
        "  SHARED_SYMPTOM_ONLY                       only the machine's output is shared",
        "  SAME_TECHNOLOGY_DIFFERENT_GOAL            same category, different blockage",
        "  GOAL_NOT_ESTABLISHED                      one or both goals are not stated",
        "",
        "WORKED EXAMPLES:",
        "",
    ]
    for example in FAMILY_WORKED_EXAMPLES:
        marker = "" if example.real else "  (illustration, not a corpus pair)"
        lines += [
            f"  {example.kind.upper()} -> {example.decision.value} / {example.reason.value}"
            f"{marker}",
            f"    A: {example.a}",
            f"    B: {example.b}",
            f"    {example.why}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


FAMILY_RUBRIC_TEXT = _render()
