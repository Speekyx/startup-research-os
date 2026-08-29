"""Credential availability, without the credential.

Mission 1.4 §16 and §37. FRED is the source that makes this necessary: its
approval carries a `CONFIG_REFERENCE` condition naming `FRED_API_KEY`, so
something has to answer *is it configured* without any part of the system
learning *what it is*.

The whole module is built around one asymmetry: a **key name** is governance
data that belongs in the registry and in this answer; a **key value** is a
secret that belongs in the environment and appears nowhere else. So:

* the only thing read from the environment is presence and emptiness;
* the returned object holds the name and a boolean, and has no field the value
  could occupy. It cannot leak from a `repr`, a log line, a JSON response or an
  exception message, because it was never in it;
* a reference that looks like a value rather than a name is refused, using the
  same rule the access-profile model applies (`source-registry-v1.md` §1.4).

**A missing credential is a normal answer, not an error.** CI has no FRED key
and must not need one: the capability of checking exists independently of
whether the deployment happens to be configured. §17 calls that distinction
"compliance capability satisfied" versus "runtime credential currently
available", and it is the reason FRED can be design-complete and still blocked.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from ..registry.models import SourceRegistryError

__all__ = ["CONFIGURED", "NOT_CONFIGURED", "CredentialStatus", "credential_status"]

CONFIGURED = "CONFIGURED"
NOT_CONFIGURED = "NOT_CONFIGURED"

# Same shapes the registry model refuses in `secret_references`. Repeated here
# rather than imported as a private name, because this is the second place a
# value could be mistaken for a name and both must refuse it.
_VALUE_MARKERS = (
    "-----begin",
    "bearer ",
    "sk-",
    "ghp_",
    "gho_",
    "github_pat_",
    "xox",
    "aiza",
    "akia",
)


@dataclass(frozen=True)
class CredentialStatus:
    """Whether a named configuration key is set. Never what it is set to.

    There is deliberately no `value` field and no accessor that could return
    one. The safety property is structural: code that wanted to leak the secret
    would have to go and read the environment itself, which is a visible change
    rather than an accidental one.
    """

    reference: str
    configured: bool

    @property
    def status(self) -> str:
        return CONFIGURED if self.configured else NOT_CONFIGURED

    def to_json(self) -> dict[str, object]:
        return {"reference": self.reference, "status": self.status}

    def __bool__(self) -> bool:
        return self.configured


def credential_status(reference: str, environ: Mapping[str, str] | None = None) -> CredentialStatus:
    """Answer CONFIGURED / NOT_CONFIGURED for one configuration key name.

    A key set to an empty or whitespace-only string counts as NOT_CONFIGURED. An
    empty variable is what a half-finished deployment leaves behind, and
    treating it as present would move the failure from a governance gate that
    explains itself to a 401 from a third party.
    """
    if not reference.strip():
        raise SourceRegistryError("credential.reference", "a configuration key name is required")
    lowered = reference.lower()
    if any(marker in lowered for marker in _VALUE_MARKERS) or len(reference) > 64:
        raise SourceRegistryError(
            "credential.reference",
            f"{reference!r} looks like a credential value rather than a configuration key "
            "name. This function takes the NAME; the value never enters the process",
        )

    source: Mapping[str, str] = environ if environ is not None else os.environ
    return CredentialStatus(reference=reference, configured=bool(source.get(reference, "").strip()))
