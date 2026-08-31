"""The use profile the runtime is operating under, declared and never inferred.

Mission 1.15.5 §12, §34, §35. Every source review answers a question about a
use. For the gate to ask the reviewer's question rather than a different one,
the runtime has to say which use it is.

**It is declared through configuration and nothing else.** Not localhost, not
Docker, not an environment name, not the number of users, not the absence of
billing. Every one of those is an infrastructural fact, and the profile is a
governance fact: the same binary in the same container can be operated under
either profile, and only a person knows which.

    SROS_USE_PROFILE=local-private-research-v1

**A profile is not an environment.** `development` and `production` say where
code runs. Startup Research OS may run in development while evaluating what a
public commercial deployment would be permitted to do, and deriving one from the
other would make that evaluation answer the wrong question.

**Missing fails closed and says so.** There is no default, because the default
that would be convenient -- the narrow local profile -- is exactly the one an
operator running a public service would most want to have been assumed for them.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping

from ..registry.models import USE_PROFILE_ID_PATTERN, SourceRegistryError

__all__ = ["USE_PROFILE_ENV_VAR", "UseProfileNotDeclaredError", "declared_use_profile"]

USE_PROFILE_ENV_VAR = "SROS_USE_PROFILE"


class UseProfileNotDeclaredError(SourceRegistryError):
    """The runtime did not say which use it is operating under.

    Deliberately a hard error rather than a `None` a caller might treat as
    "unknown, carry on". Nothing downstream can make a correct permission
    decision without this, so there is nothing useful to carry on with.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(USE_PROFILE_ENV_VAR, reason)


def declared_use_profile(environ: Mapping[str, str] | None = None) -> str:
    """The declared profile id, or a refusal.

    `environ` is injectable for the same reason it is elsewhere in this package:
    a test that had to mutate the real environment to exercise a governance
    boundary would leak into every test that ran after it.
    """
    source: Mapping[str, str] = environ if environ is not None else os.environ
    declared = (source.get(USE_PROFILE_ENV_VAR) or "").strip()

    if not declared:
        raise UseProfileNotDeclaredError(
            "not set. Acquisition authorization requires the runtime to declare which "
            "assessed use profile it is operating under, and it is never inferred from "
            "the environment name, the host, the container or the user count "
            f"(Mission 1.15.5 §12). Set {USE_PROFILE_ENV_VAR} to a registered profile "
            "id, for example local-private-research-v1"
        )
    if not re.match(USE_PROFILE_ID_PATTERN, declared):
        raise UseProfileNotDeclaredError(
            f"{declared!r} is not a use-profile id. Expected a slug carrying its "
            f"semantic version, matching {USE_PROFILE_ID_PATTERN}"
        )
    return declared
