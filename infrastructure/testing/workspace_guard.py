"""Refuse to point a destructive test fixture at persistent development data.

Mission 1.6.1 §17. Stdlib only, no database, no dependency: a guard that needs
an install is a guard that stops running the day an environment breaks.

WHY THIS EXISTS AT ALL

Three separate incidents in one afternoon, all the same shape:

  * a claim suite wrote 39 claims and 36 evidence rows into the seeded
    development workspace and never removed them;
  * `test_rls.py` proved that an unscoped `DELETE FROM research.research_projects`
    cannot cross a tenant boundary -- by running it inside the seeded workspace,
    which deleted a real research session and orphaned twelve records;
  * an acquisition fixture deleted raw and normalized records from seeded
    workspace B in teardown, harmlessly, because B happened to be empty.

None of them was careless. Each test was correct about the property it asserted;
each had simply reached for the workspace id that was already in scope.

WHY IT IS A FUNCTION AND NOT A CONVENTION

The runner's post-suite leak check (`run_pytest_suites.py`) catches a suite that
CHANGES the database, which is the right net-effect guard and cannot see the
third case above: deleting from an empty seeded workspace nets to zero today and
destroys real data the moment somebody collects into it.

So this is the other half. The leak check asks "did the run change anything";
this asks "is this fixture even allowed to point here", before it runs.

    disposable(workspace_id)   -> the id, or raises

Call it in the fixture that CREATES or DESTROYS, not at every use site. A guard
you have to remember everywhere is one you will forget somewhere.
"""

from __future__ import annotations

import uuid

__all__ = [
    "SEEDED_WORKSPACES",
    "SeededWorkspaceError",
    "disposable",
    "is_seeded",
]

# The workspaces `infrastructure/db/seed/0001_dev_workspace.sql` creates. They
# are reference data every suite may READ, they hold real collected records, and
# no test may create or destroy them.
#
# Written as literals rather than read from the seed file on purpose: this must
# work with no database and no parsing, and a guard whose input can fail open is
# not a guard.
SEEDED_WORKSPACES: frozenset[uuid.UUID] = frozenset(
    {
        uuid.UUID("00000000-0000-4000-8000-000000000001"),  # dev
        uuid.UUID("00000000-0000-4000-8000-000000000003"),  # dev-other
    }
)


class SeededWorkspaceError(AssertionError):
    """A destructive fixture was pointed at persistent development data.

    An `AssertionError` so pytest reports it as a failed test rather than as an
    error in the harness -- the test IS wrong, and that is the message.
    """


def is_seeded(workspace_id: uuid.UUID | str) -> bool:
    """Whether this is one of the seeded development workspaces."""
    try:
        parsed = (
            workspace_id if isinstance(workspace_id, uuid.UUID) else uuid.UUID(str(workspace_id))
        )
    except (ValueError, AttributeError, TypeError):
        # Not a uuid at all. Not seeded, and whatever is wrong with it is the
        # caller's problem to report, not this function's to hide.
        return False
    return parsed in SEEDED_WORKSPACES


def disposable(workspace_id: uuid.UUID | str, *, what: str = "this fixture") -> uuid.UUID | str:
    """Return the id, or refuse it because it is seeded development data.

    Returns the argument unchanged so it reads naturally at the point of use:

        _make_workspace(disposable(WORKSPACE_P, what="the acquisition probe"))

    `what` is the fixture's own name, because the failure message has to say
    which fixture to fix -- a stack trace through pytest's fixture machinery
    does not make that obvious.
    """
    if is_seeded(workspace_id):
        raise SeededWorkspaceError(
            f"{what} was pointed at seeded development workspace {workspace_id}.\n"
            "\n"
            "That workspace is created by infrastructure/db/seed/0001_dev_workspace.sql, "
            "is shared by every suite, and holds real collected records. A fixture that "
            "creates or destroys it decides what other suites can test, and deletes data "
            "somebody collected.\n"
            "\n"
            "Use a workspace of this suite's own: create it in the fixture, drop it in "
            "teardown, and give it an id no other suite uses. Reading seeded data is fine; "
            "writing to it is what this refuses.\n"
            "\n"
            "See docs/testing/test-data-isolation-audit-v1.md."
        )
    return workspace_id
