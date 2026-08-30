# ADR-018 — Record what KIND of thing authorises a resource, not only which licence

- **Status:** Accepted
- **Date:** 2026-08-30
- **Deciders:** Mission 1.9.1
- **Supersedes:** none
- **Related:** Mission 1.9.1 §13–§16, §28;
  [`acquisition-rights-basis-gap-analysis-v1.md`](../../data/acquisition-rights-basis-gap-analysis-v1.md);
  [ADR-016](ADR-016-compliance-capabilities-and-acquisition-authorization.md);
  [`gdelt-compliance-v1.md`](../../data/gdelt-compliance-v1.md)

---

## Context

`AuthorizedDataset` has required a non-empty `licence` since Mission 1.4, and
every source that has ever had one satisfies it naturally: World Bank datasets
are `CC-BY-4.0` or `ODbL-1.0`, Eurostat's are governed by a copyright notice,
FRED's by its terms. Each is a **named instrument** that can be written down and
matched against an allowlist.

GDELT is the first approved source that has no licence to name. Its terms grant
use directly:

> all datasets released by the GDELT Project are available for unlimited and
> unrestricted use for any academic, commercial or governmental use of any kind
> without fee

That is a broader grant than most licences give, and it is not a licence. The
model had no way to say so, so a GDELT dataset entry could not be written at all
— which is **H-28**, and which blocked the resource model the collector needs.

`gdelt-compliance-v1.md` §2 had already recorded the same fact from the
attribution side: GDELT gets no `LICENCE_IDENTIFIER` element "because GDELT names
no licence: it grants unlimited use directly rather than through a named
instrument". The dataset model needed the same honesty available to it.

**The decision was constrained by one hard requirement.** Mission 1.9.1 §15: the
change must not weaken any source whose authorisation genuinely depends on a
named licence. World Bank's does — its platform distributes under several
licences and the wrong one carries obligations nobody accepted.

## Decision

An authorised dataset records a **`RightsBasis`** — a closed enum of
`NAMED_LICENCE | DIRECT_GRANT` — and `licence` becomes conditional on it:
required under `NAMED_LICENCE`, and **required to be absent** under
`DIRECT_GRANT`. A licence allowlist is satisfied only by a `NAMED_LICENCE`
resource, so a direct grant is refused by it rather than passing it by having
nothing to compare.

## Alternatives considered

### Alternative A — put a placeholder in the licence field

`"OTHER"`, `"GDELT Terms Licence"`, `"NONE"`, `"N/A"`. No code change, one
config line.

Rejected because each is a different lie. `"OTHER"` asserts there is a licence of
an unenumerated kind; `"GDELT Terms Licence"` asserts GDELT publishes an
instrument by that name, which it does not and which would be **this
repository's invention presented as the source's**; `"NONE"` reads as unlicensed
when the resource is in fact permitted.

All of them put an answer to *which licence?* in a field whose real answer is
*that is the wrong question for this source* — and the string would land in
every authorised record's provenance, where a later reader could not tell it
from `CC-BY-4.0`.

### Alternative B — make `licence` optional and leave it at that

One-line change: drop the non-empty requirement.

Rejected because it is silently permissive in the direction that matters. A
`None` licence would then mean *either* "authorised by a direct grant" *or*
"somebody forgot", and the licence-allowlist rule would have to guess which. It
also gives no place to record that the absence was **reviewed**.

### Alternative C — a free-text `rights_note` instead of an enum

More expressive, no contract change.

Rejected because authorization code has to branch on this. A free-text field
cannot be branched on without pattern-matching prose, which is the failure
`AcquisitionErrorCode` and `NormalizationErrorCode` are both closed enums to
avoid: a consumer branching on a message breaks when the message is reworded.

### Alternative D — add an `UNKNOWN` member

Symmetry with `ResourceContentOrigin`, which has one.

Rejected, and the asymmetry is deliberate. `ResourceContentOrigin.UNKNOWN`
exists because "who owns this?" is a question with a genuine third state that
must fail closed. "What authorises this?" has no third state: an unestablished
basis is the **absence** of a basis, which the model already expresses as `None`
and refuses. A member spelled `UNKNOWN` would be a value that *looks* like an
answer, and would end up written into config by somebody who did not want to
decide.

## Pros

- **GDELT's grant is representable truthfully**, with no invented identifier
  reaching any record's provenance.
- **The licence allowlist got stricter, not looser.** It now requires the basis
  *and* the identifier, where before it required only the identifier — a
  descriptor with no basis at all used to pass if it carried a licence string.
- **Both fabrications are refused**: a `NAMED_LICENCE` with no name, and a
  `DIRECT_GRANT` carrying one.
- **No default.** The loader refuses an entry that omits the basis, so the first
  entry that forgets is a failure rather than a silent mis-classification.
- No database migration, and no stored record altered.

## Cons

- **A contract enum is hard to reverse.** `RightsBasis` is generated into
  TypeScript and Python and versioned; removing it later means a contract change
  with the same ceremony as adding it.
- **Two values will not be enough forever.** Public domain, a statutory
  exception and a negotiated contract are all plausible future bases, and each
  would be a contract change. Adding them now would be speculative vocabulary
  nobody has reviewed, so the cost is deferred deliberately rather than avoided.
- **Three existing config entries had to be edited**, which §16 would have
  preferred to avoid. Inferring the basis from the presence of a licence would
  have avoided it and is exactly the silent default the previous point rejects.
- **It records a reviewed basis; it does not evaluate one.** The model has no
  opinion about whether a direct grant is legally sufficient — a reviewer
  decided that. `source-registry-v1.md` §0 is unchanged, and this ADR must not
  be read as making the system a legal decision engine.

## Consequences

- `RightsBasis` joins the closed enums in
  `packages/contracts/schema/domain.v1.json`, generated into both runtimes.
- `AuthorizedDataset` gains `rights_basis` (required, no default) and `licence`
  becomes `str | None`, validated against the basis in both directions.
- `ResourceDescriptor` gains `rights_basis`, defaulting to `None` — "not
  established", which every rule that cares about rights treats as a refusal.
- `authorize_resource` requires `NAMED_LICENCE` wherever a licence allowlist is
  configured, and reports a basis mismatch distinctly from a missing licence:
  the two call for different fixes.
- The World Bank collector carries the basis from the authorised dataset into
  the descriptor it builds, because that is the only path a descriptor is
  supposed to come from.
- **H-28 is closed.** H-27 is not, so no GDELT dataset entry is committed yet:
  what a GDELT resource *is* depends on which API mode the collector uses.
