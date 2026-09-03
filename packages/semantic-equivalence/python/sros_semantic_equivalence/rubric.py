"""The equivalence rubric: three outcomes and one fixed granularity.

Mission 1.24 §4 and §5, from `semantic-problem-equivalence-v1.md` §4.2.

**Granularity is decided ONCE, here, and never per pair.** A classifier allowed
to pick its own abstraction level will pick a convenient one, and the convenient
level is whichever makes the current pair easy: *both are Docker problems* is
always available and always useless.

**The question is NOT "do these share a true root cause".** Question text often
cannot establish a root cause -- the asker frequently does not know it, which is
why they are asking. Asking for one would force the classifier to guess and then
report the guess as an equivalence.

**ABSTAIN is mandatory and is not a failure.** Two outcomes would force a choice
on text that supports neither, and a forced choice on this corpus is a false
SAME, which V1 treats as worse than no answer at all.

**Mission 1.20's trio constrains this definition rather than illustrating it.**
Three questions share 106 characters of exact Docker daemon and runc diagnostic
and then diverge into `permission denied` on an entrypoint script, a missing
`pipenv` binary, and `gunicorn` absent from `$PATH`. A rubric that groups them
has failed, whatever it scores elsewhere -- so the wrapper is named in the
insufficient list rather than left to judgement.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "RUBRIC_VERSION",
    "EquivalenceDecision",
    "ReasonCode",
    "GRANULARITY",
    "INSUFFICIENT_ALONE",
    "WORKED_EXAMPLES",
    "WorkedExample",
    "RUBRIC_TEXT",
]

RUBRIC_VERSION = "problem-equivalence-rubric@1.0.0"


class EquivalenceDecision(StrEnum):
    """The three outcomes. Closed, and ABSTAIN is not a degraded SAME."""

    SAME_PROBLEM = "SAME_PROBLEM"
    DIFFERENT_PROBLEM = "DIFFERENT_PROBLEM"
    ABSTAIN = "ABSTAIN"


class ReasonCode(StrEnum):
    """Why the decision came out that way.

    **Derived from the pairs this corpus actually produces**, not adopted from a
    list. Each was written against an observed candidate pair, named in its
    docstring below, so the vocabulary answers a real distinction rather than an
    anticipated one.

    Free text is required alongside a code but is never the only audit surface:
    prose cannot be counted, grouped or compared across a run, and an evaluation
    whose only artefact is prose is one nobody can score.
    """

    #: The runc trio: 78086542 / 78099519 / 78099680. An identical container
    #: runtime wrapper, then `permission denied`, `no such file or directory`
    #: and `executable file not found in $PATH`. The wrapper names the envelope;
    #: the failure is what comes after it.
    SHARED_WRAPPER_DIVERGENT_TERMINAL_CAUSE = "SHARED_WRAPPER_DIVERGENT_TERMINAL_CAUSE"

    #: 78093369 (psycopg on alpine, missing build toolchain) with 78105004
    #: (rails/kamal, apt-get cannot install libc-bin). Both are a Docker build
    #: that ends in `exit code: 1`, which is every failed build ever.
    SHARED_GENERIC_ERROR_ONLY = "SHARED_GENERIC_ERROR_ONLY"

    #: 78096355 (Spring Boot scheduled logs not visible) with 78097579 (Spring
    #: Boot port not exposed). Same framework, same tags, different subsystem
    #: and a fix to one teaches nothing about the other.
    SAME_STACK_DIFFERENT_CONCERN = "SAME_STACK_DIFFERENT_CONCERN"

    #: The justification a SAME decision must carry: the same component, the
    #: same class of misconfiguration or defect, one fix answering both.
    SAME_ACTIONABLE_FAILURE = "SAME_ACTIONABLE_FAILURE"

    #: 78097071 asks how to set up a database through an npm package and reports
    #: no failure at all. A pair containing it cannot be decided, because one
    #: side has no actionable failure to compare.
    INSUFFICIENT_DETAIL = "INSUFFICIENT_DETAIL"


# ---------------------------------------------------------------------------
# The granularity, stated operationally so two reviewers can disagree about a
# pair and still agree about what they are disagreeing over.

GRANULARITY = """\
Two published question descriptions concern the SAME actionable technical failure
concept when a reader who had the working fix for one would, from that fix alone,
know what to change for the other -- and the change would be to the same
component, addressing the same class of misconfiguration or defect.

This is a question about the PUBLISHED DESCRIPTIONS, not about the underlying
truth. Question text often cannot establish a root cause, because the asker
usually does not know it. Where the text does not support a decision, the answer
is ABSTAIN.\
"""

# Each of these is a real property of pairs this corpus produces, and each is
# insufficient BY CONSTRUCTION rather than below some threshold. A threshold
# would invite the question "how much shared wrapper is enough", and the answer
# is that no amount is.
INSUFFICIENT_ALONE: tuple[str, ...] = (
    "the same tool, runtime or platform (every question here is a Docker question)",
    "the same site tags",
    "the same wrapper or harness diagnostic, however long the shared string",
    "the same generic error class -- permission denied, connection refused, exit code 1, "
    "HTTP 500, a bare ValueError",
    "the same broad symptom, such as 'the container will not start' or 'the page will not load'",
    "the same language, framework or base image",
)


@dataclass(frozen=True)
class WorkedExample:
    """One decided pair, with the reasoning that decides it.

    `real` marks whether the pair exists in the corpus. The rubric needs a
    qualifying example in order to fix granularity, and at the time of writing
    **no SAME pair has been confirmed in this corpus** -- so the qualifying
    example is a constructed illustration and says so. It defines the rubric; it
    is never evidence about the model, and §20 forbids treating it as any.
    """

    kind: str
    decision: EquivalenceDecision
    reason: ReasonCode
    a: str
    b: str
    why: str
    real: bool


WORKED_EXAMPLES: tuple[WorkedExample, ...] = (
    WorkedExample(
        kind="qualifying",
        decision=EquivalenceDecision.SAME_PROBLEM,
        reason=ReasonCode.SAME_ACTIONABLE_FAILURE,
        a="a compose service cannot reach its database, and the description shows the host "
        "set to a name no service in the file defines",
        b="a compose service cannot reach its database, and the description shows the host "
        "set to `localhost` from inside a container",
        why=(
            "ILLUSTRATION, NOT A CORPUS PAIR. Both descriptions are the same actionable "
            "concept: the database host a container is configured with does not resolve to "
            "the database on the compose network. One fix -- point the host at the compose "
            "service name -- answers both, and the change is to the same component. It is "
            "written out because a rubric with no qualifying example defines a boundary with "
            "only one side. No SAME pair had been confirmed in this corpus when it was written"
        ),
        real=False,
    ),
    WorkedExample(
        kind="non-qualifying",
        decision=EquivalenceDecision.DIFFERENT_PROBLEM,
        reason=ReasonCode.SHARED_WRAPPER_DIVERGENT_TERMINAL_CAUSE,
        a='78086542 -- OCI runtime create failed ... exec: "/usr/src/app/entrypoint.sh": '
        "permission denied",
        b='78099680 -- OCI runtime create failed ... exec: "gunicorn": executable file not '
        "found in $PATH",
        why=(
            "The canonical hard negative, and the reason this rubric exists. 106 characters "
            "of identical daemon and runc diagnostic, and then a file-mode problem on a script "
            "the image contains versus a binary the image does not contain. The fix for one "
            "teaches nothing about the other. A rubric that groups these has failed whatever "
            "it scores elsewhere"
        ),
        real=True,
    ),
    WorkedExample(
        kind="borderline",
        decision=EquivalenceDecision.DIFFERENT_PROBLEM,
        reason=ReasonCode.SAME_STACK_DIFFERENT_CONCERN,
        a="78088430 -- a Wordpress compose stack that serves fine until about ten concurrent "
        "reloads, then reports 'Error Establishing a Database Connection' while every "
        "container stays up",
        b="78090396 -- a Wordpress compose stack whose web UI never loads at all, with a "
        "database host written as a malformed environment entry",
        why=(
            "BORDERLINE, AND DECIDED. Same product, same tags, same subsystem, and the same "
            "words could describe both symptoms. But one is a capacity or connection-limit "
            "problem under load in a working deployment, and the other is a deployment that "
            "has never worked because of a configuration error. Neither fix helps the other, "
            "so the shared symptom is a surface. This is where the granularity definition does "
            "its work: the question is what a reader would CHANGE, not what the page says"
        ),
        real=True,
    ),
    WorkedExample(
        kind="abstention",
        decision=EquivalenceDecision.ABSTAIN,
        reason=ReasonCode.INSUFFICIENT_DETAIL,
        a="78097071 -- how to set up a database through an npm package in a Docker container, "
        "reporting no failure at all",
        b="78096175 -- a postgres volume whose data does not survive a re-run",
        why=(
            "One side describes no failure, so there is no actionable failure concept to "
            "compare it against. ABSTAIN is the correct answer and not a degraded DIFFERENT: "
            "saying DIFFERENT would assert that the two concepts are distinct, when one of "
            "them was never established"
        ),
        real=True,
    ),
)


def _render_rubric() -> str:
    """The rubric as the classifier receives it.

    Rendered from the same constants the code and the tests use, so the text a
    model reads cannot drift from the definition this module enforces. A prompt
    with its own hand-written copy of the rules is a second rubric.
    """
    lines = [
        "GRANULARITY -- the level at which this question is asked, fixed for every pair:",
        "",
        GRANULARITY,
        "",
        "OUTCOMES -- exactly three:",
        "",
        "  SAME_PROBLEM       the descriptions concern the same actionable failure concept",
        "  DIFFERENT_PROBLEM  they concern different actionable failure concepts",
        "  ABSTAIN            the published text cannot support either answer",
        "",
        "ABSTAIN is a correct answer, not a failure to answer. Prefer it whenever the text",
        "does not establish the actionable concept on both sides. A wrong SAME_PROBLEM is",
        "the most costly error this task can make.",
        "",
        "INSUFFICIENT ALONE -- none of the following, on its own or in combination with",
        "others from this list, makes two descriptions the same problem:",
        "",
    ]
    lines += [f"  - {item}" for item in INSUFFICIENT_ALONE]
    lines += ["", "REASON CODES -- exactly one per decision:", ""]
    lines += [
        "  SHARED_WRAPPER_DIVERGENT_TERMINAL_CAUSE  a shared wrapper diagnostic, then "
        "different terminal causes",
        "  SHARED_GENERIC_ERROR_ONLY                only a generic error class in common",
        "  SAME_STACK_DIFFERENT_CONCERN             same technology, different subsystem "
        "or operation",
        "  SAME_ACTIONABLE_FAILURE                  one fix would answer both, in the same "
        "component",
        "  INSUFFICIENT_DETAIL                      one or both descriptions do not "
        "establish an actionable failure",
        "",
        "WORKED EXAMPLES:",
        "",
    ]
    for example in WORKED_EXAMPLES:
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


RUBRIC_TEXT = _render_rubric()
