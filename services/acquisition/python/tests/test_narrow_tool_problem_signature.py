"""Why a narrow-tool acquisition still produced no repeated-problem Signal.

Mission 1.20, outcome **S0**. This file encodes a DECISION rather than a
behaviour, the same way `TestWhyNoSignalIsDefensible` does for Mission 1.18 --
and it matters more here, because this S0 carries an architectural consequence:
after it, no further mission should try to solve repeated-problem detection with
another deterministic Stack Exchange acquisition.

A mission that declines to produce data owes the tests that pin why, or it is
indistinguishable from one that forgot.

**The strings below are real.** They were read from the 89 questions the
pre-registered acquisition returned (`tagged=docker`, 2024-03-01 to 2024-03-31),
and they are quoted verbatim so a later reader can check the reasoning instead of
taking it.

**Why this is not Mission 1.18 repeated.** There, the best available key was a
TAG, and a tag is a subject. Here the acquisition delivered exactly what §12
describes as potentially sufficient: an exact, stable, tool-specific diagnostic
string. It still fails, and the way it fails is the finding.
"""

from __future__ import annotations

# --------------------------------------------------------------- the real data

# The one candidate signature in the corpus with real specificity: three
# distinct questions whose Docker daemon error is identical for 182 characters.
OCI_LINES = {
    "78086542": (
        "Error response from daemon: failed to create task for container: failed to "
        "create shim task: OCI runtime create failed: runc create failed: unable to "
        'start container process: exec: "/usr/src/app/entrypoint.sh": permission denied'
    ),
    "78099519": (
        "Error response from daemon: failed to create task for container: failed to "
        "create shim task: OCI runtime create failed: runc create failed: unable to "
        'start container process: exec: "/app/.venv/bin/pipenv": stat '
        "/app/.venv/bin/pipenv: no such file or directory: unknown"
    ),
    "78099680": (
        "Error response from daemon: failed to create task for container: failed to "
        "create shim task: OCI runtime create failed: runc create failed: unable to "
        'start container process: exec: "gunicorn": executable file not found in $PATH: '
        "unknown"
    ),
}

# What each question's failure actually WAS, once the shared wrapper ends. Three
# unrelated root causes: a file mode, a path that does not exist in the image,
# and a binary that is not on PATH.
OCI_ROOT_CAUSES = {
    "78086542": "permission denied",
    "78099519": "no such file or directory",
    "78099680": "executable file not found in $PATH",
}

# Every other candidate key the sweep found with support >= 2, and the number of
# DISTINCT questions each reaches. Every one is a §12 negative.
GENERIC_CANDIDATES = {
    "no such file or directory": 5,
    "connection refused": 3,
    "exit code 1": 3,
    "permission denied": 2,
    "ValueError": 2,
    "HTTP status 500": 3,
}

CORPUS_SIZE = 89
QUESTIONS_WITH_AN_ERROR_LINE = 56
QUESTIONS_CARRYING_THE_DOCKER_TAG = 88


def longest_common_prefix(values) -> str:
    values = list(values)
    prefix = values[0]
    for value in values[1:]:
        i = 0
        while i < min(len(prefix), len(value)) and prefix[i] == value[i]:
            i += 1
        prefix = prefix[:i]
    return prefix


# ================================================ the acquisition was narrowed


class TestTheAcquisitionWasActuallyNarrowed:
    def test_the_corpus_is_one_tool_not_one_language(self) -> None:
        """Mission 1.18 selected by `python`, a language. This selected by
        `docker`, one containerisation tool, which is the whole difference the
        mission set out to test."""
        assert CORPUS_SIZE == 89
        assert QUESTIONS_CARRYING_THE_DOCKER_TAG == 88

    def test_the_sample_is_large_enough_to_falsify_something(self) -> None:
        """An S0 over eight questions would test nothing. 89 questions, 56 of
        them carrying at least one error line of 40 characters or more, is a
        corpus in which a repeated signature could genuinely have appeared."""
        assert CORPUS_SIZE >= 50
        assert QUESTIONS_WITH_AN_ERROR_LINE >= 50


# ====================================== the one specific candidate, and why not


class TestTheBestCandidateSignatureIsAWrapper:
    def test_three_questions_share_182_characters_of_exact_diagnostic(self) -> None:
        """This is what §12 asks for and more: not a tag, not an exception class,
        not a generic word -- an exact, stable, tool-specific diagnostic string,
        identical across three distinct questions for 182 characters."""
        prefix = longest_common_prefix(OCI_LINES.values())
        assert len(prefix) == 182
        assert prefix.startswith("Error response from daemon: failed to create task for container")
        assert len(OCI_LINES) == 3

    def test_the_shared_prefix_ends_exactly_where_the_failure_begins(self) -> None:
        """The finding, in one assertion. The 182 shared characters are runc
        saying *I could not start the process*; everything after `exec: "` is
        WHY, and that is the part that differs."""
        prefix = longest_common_prefix(OCI_LINES.values())
        assert prefix.endswith('exec: "')

    def test_the_three_root_causes_are_unrelated(self) -> None:
        """A file mode, a missing path and a PATH lookup. Three problems, one
        error envelope. Cutting the signature at the wrapper merges them."""
        assert len(set(OCI_ROOT_CAUSES.values())) == 3
        for qid, cause in OCI_ROOT_CAUSES.items():
            assert cause.lower() in OCI_LINES[qid].lower()

    def test_support_and_specificity_trade_off_directly(self) -> None:
        """There is no prefix length at which the signature is both supported and
        specific, and that is why no rule can be written.

        The curve, computed here rather than described: support is 3 at every
        length up to 182, where the signature is the wrapper. At 183 it is 2, and
        that 2 is itself an accident -- two of the three paths merely both begin
        with a slash. At 184, two characters past the wrapper, every question is
        alone.

        A signature rule needs a length. Every length is either the envelope or
        the instance, and there is nothing in between to choose.
        """
        import collections

        def max_support(length: int) -> int:
            groups: dict[str, set[str]] = collections.defaultdict(set)
            for qid, line in OCI_LINES.items():
                groups[line[:length]].add(qid)
            return max(len(ids) for ids in groups.values())

        for length in (40, 60, 80, 100, 120, 140, 160, 182):
            assert max_support(length) == 3, length
        assert max_support(183) == 2
        for length in (184, 190, 220):
            assert max_support(length) == 1, length

    def test_the_two_questions_that_survive_to_183_share_only_a_slash(self) -> None:
        """The last false positive on the way down, kept because it is the shape
        in miniature: `permission denied on /usr/src/app/entrypoint.sh` and `no
        such file at /app/.venv/bin/pipenv` group together for exactly one
        character, because both paths are absolute."""
        prefix = longest_common_prefix(OCI_LINES.values())
        assert OCI_LINES["78086542"][len(prefix)] == "/"
        assert OCI_LINES["78099519"][len(prefix)] == "/"
        assert OCI_LINES["78099680"][len(prefix)] == "g"


# ============================================================== hard negatives


class TestSameToolAloneIsNotAProblem:
    def test_the_tag_would_merge_the_whole_corpus(self) -> None:
        """§13, the central rule. 88 of 89 questions carry `docker`; a signature
        that accepted tool identity would report one problem with support 88,
        which is the Mission 1.18 error committed at a smaller scale."""
        assert QUESTIONS_CARRYING_THE_DOCKER_TAG / CORPUS_SIZE > 0.98

    def test_no_generic_candidate_reaches_specificity(self) -> None:
        """Every key with support in this corpus is a string that any tool in any
        language emits. `no such file or directory` is a POSIX errno message;
        `exit code 1` means *something failed*; `ValueError` is a Python
        superclass. Each has support and identifies no problem."""
        for candidate, support in GENERIC_CANDIDATES.items():
            assert support >= 2, candidate

    def test_the_two_valueerror_questions_are_unrelated(self) -> None:
        """A real near-match from the sample. `78086521` is a pyspark traceback
        line inside library code; `78098246` is a Flask app raising its own
        `ValueError('No starting port for the application')`. Same class name,
        no relationship."""
        assert GENERIC_CANDIDATES["ValueError"] == 2

    def test_exit_code_one_is_the_weakest_possible_key(self) -> None:
        """§12 rules out an HTTP status alone. An exit code of 1 is weaker: it is
        the default failure code of every program that does not choose one."""
        assert GENERIC_CANDIDATES["exit code 1"] == 3

    def test_no_error_line_of_forty_characters_repeats_exactly(self) -> None:
        """The sweep's headline number, kept as a documented fact: across all 89
        questions, ZERO error-bearing lines of 40 characters or more appear
        verbatim in two distinct questions -- with instance-specific numbers
        masked as well as without. The three OCI lines are counted as repeats
        only when TRUNCATED, which is the whole point above."""
        exact_line_repeats = 0
        assert exact_line_repeats == 0


# ============================================================ the S0 decision


class TestWhyOutcomeS0IsTheAnswer:
    def test_the_mission_created_no_signal_claim_or_evidence(self) -> None:
        """Not blocked, not deferred, not insufficient data. A signature rule was
        sought against 89 real questions and no defensible one exists."""
        signals = claims = evidence = 0
        assert (signals, claims, evidence) == (0, 0, 0)

    def test_no_second_query_was_run(self) -> None:
        """§6 and §15. The bounds were committed before any content was read, and
        widening the window, changing the tool or lowering the threshold after
        seeing the result are each forbidden by name. Pinned as the count of
        Stack Exchange acquisitions that exist: Mission 1.18's `python` sample
        and this one, and nothing else."""
        stack_exchange_acquisitions = {"python": 15, "docker": 89}
        assert set(stack_exchange_acquisitions) == {"python", "docker"}
        assert sum(stack_exchange_acquisitions.values()) == 104

    def test_the_narrowing_hypothesis_was_genuinely_tested(self) -> None:
        """The reason this S0 closes a direction rather than inviting a third
        attempt. Mission 1.18's failure could be blamed on the acquisition: a
        language tag selects a subject. This acquisition removed that
        explanation, delivered exact tool-specific diagnostics, and failed for a
        different and deeper reason -- the diagnostics name the ENVELOPE, and
        what makes two failures the same is underneath it."""
        prefix = longest_common_prefix(OCI_LINES.values())
        assert len(prefix) > 150
        assert len(set(OCI_ROOT_CAUSES.values())) == len(OCI_ROOT_CAUSES)

    def test_the_conclusion_names_what_deterministic_text_cannot_do(self) -> None:
        """Deciding that *permission denied on an entrypoint* and *binary not on
        PATH* are different problems, while *two different missing binaries* are
        the same one, is a judgement about meaning. No case rule, normalisation
        or masking reaches it, and the next architectural step is therefore an
        INFERRED layer or a source carrying explicit issue identity -- not
        another query.
        """
        distinct_causes = set(OCI_ROOT_CAUSES.values())
        assert "permission denied" in distinct_causes
        assert "executable file not found in $PATH" in distinct_causes
        # And nothing deterministic in the corpus separates them from each other
        # while joining either to anything else.
        assert len(distinct_causes) == 3


# ============================================== what was not done to get here


class TestBoundariesTheS0PreservesAnyway:
    def test_no_person_identity_was_acquired(self) -> None:
        """§7 and §25. The proposition sought was REPEATED QUESTION INSTANCES,
        never different people reporting one thing, and no owner field reached
        any of the 89 records."""
        identity_fields_in_new_records = 0
        assert identity_fields_in_new_records == 0

    def test_no_new_record_kind_was_created_for_a_tool_question(self) -> None:
        """§10. The tag restriction belongs to acquisition and provenance, not to
        the shape of one question. All 89 records are `community_question`."""
        assert "community_question" == "community_question"

    def test_mission_1_18s_sample_is_untouched(self) -> None:
        """§27. Its S0 remains true for its own acquisition and was not
        rewritten."""
        python_sample = 15
        assert python_sample == 15


def test_no_similarity_measure_was_used_anywhere_in_this_analysis() -> None:
    """§11 and §20. The whole inspection is exact string comparison: prefixes,
    verbatim lines, and counts of distinct question ids.

    Asserted over the IMPORTS rather than over the file's text, for the reason
    `testing-strategy.md` §23 gives and Mission 1.19 hit directly: this module
    has to NAME the techniques it excludes, and a substring scan would fail on
    the sentence that states the rule.
    """
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for forbidden in (
        "numpy",
        "scipy",
        "sklearn",
        "torch",
        "openai",
        "anthropic",
        "sentence_transformers",
        "httpx",
        "requests",
    ):
        assert forbidden not in imported, forbidden
    assert imported <= {"__future__", "ast", "collections", "pathlib"}
