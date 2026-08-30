# Acquisition Rights Basis Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.9.1 §13, **before**
`AuthorizedDataset` changed.
**Date:** 2026-08-30
**Reads:** `sros_acquisition.compliance.config.AuthorizedDataset`,
`compliance/resources.py`, `compliance/capabilities.py`, and the four committed
entries in [`source-compliance-v1.json`](source-compliance-v1.json).
**Related:** [`acquisition-authorization-v1.md`](acquisition-authorization-v1.md),
[`gdelt-compliance-v1.md`](gdelt-compliance-v1.md),
[`gdelt-raw-record-gap-analysis-v1.md`](gdelt-raw-record-gap-analysis-v1.md) §9.2,
[ADR-016](../architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md).

---

## 0. The problem, stated exactly

`AuthorizedDataset` requires a non-empty `licence`:

```python
for field_name in ("resource_id", "dataset_family", "licence", "content_origin"):
    if not str(getattr(self, field_name)).strip():
        raise SourceRegistryError(f"dataset.{field_name}", "required")
```

Every source that has ever had an authorised dataset satisfies it naturally.
World Bank datasets are `CC-BY-4.0`, Eurostat's are governed by a copyright
notice, FRED's by its terms — each a **named instrument** that can be written
down and matched against an allowlist.

**GDELT has no named licence.** Its terms grant use directly:

> all datasets released by the GDELT Project are available for unlimited and
> unrestricted use for any academic, commercial or governmental use of any kind
> without fee

That is a broader grant than most licences give, and it is not a licence. There
is nothing to name.

## 1. Why the obvious answers are all wrong

Each of these was considered and each is a lie of a different shape.

| Value | What it asserts | Why it is false |
|---|---|---|
| `"OTHER"` | there is a licence, of an unenumerated kind | there is no licence |
| `"GDELT Terms Licence"` | GDELT publishes an instrument by that name | **it does not.** The string would be this repository's invention presented as the source's |
| `"NONE"` | the resource is unlicensed | it is *permitted*, which is the opposite of what a reader would take from `NONE` |
| `"N/A"` | the question does not apply | it applies and has an answer |
| `""` | nothing is known | the model already refuses this, correctly |

The common failure is that **all five put an answer to "which licence?" in a
field whose real answer is "that is the wrong question for this source"**. The
model has no way to say that, and inventing a string to fill the field would put
a fabricated fact into every record's provenance, where a later reader would
have no way to tell it apart from `CC-BY-4.0`.

`gdelt-compliance-v1.md` §2 already records this from the attribution side:
GDELT gets no `LICENCE_IDENTIFIER` element "because GDELT names no licence: it
grants unlimited use directly rather than through a named instrument, which is
unusual and is why LICENCE_IDENTIFIER is absent rather than blank."

The dataset model needs the same honesty available to it.

## 2. What the field is actually for

Three consumers, and they want different things:

| Consumer | Uses | Needs |
|---|---|---|
| `authorize_resource` licence allowlist | `descriptor.licence ∈ scope.licence_allowlist` | a **matchable identifier** |
| `render_attribution` | `AttributionFacts(licence_identifier=…)` | a **displayable name**, and only when the obligation requires one |
| RawRecord provenance | `"licence": dataset.licence` | a **record of what authorised this**, for a reader years later |

The third is the one that matters here and it is the one the current model
serves worst. A provenance entry saying `"licence": "GDELT Terms Licence"` would
be unauditable — nobody could find that instrument, because it does not exist.

What a reader actually needs to know is: **on what basis were we allowed to hold
this?**

## 3. The model

The smallest change that can express both cases truthfully.

### 3.1 A closed enum, because code branches on it exhaustively

```text
RightsBasis = NAMED_LICENCE | DIRECT_GRANT
```

`NAMED_LICENCE` — a published instrument authorises the resource, and it has an
identifier. World Bank, Eurostat, FRED.

`DIRECT_GRANT` — the source's own terms grant the use directly, naming no
instrument. GDELT.

Closed rather than a registry (Ontology V2 §14.2): the authorization code
branches exhaustively, and an unhandled third value would mean a resource of
unknown standing being treated as authorised. That is the same argument
`SourceApprovalState` is closed for.

**Two values, not three.** There is no `UNKNOWN` member: an unestablished basis
is the *absence* of a basis, which the model already expresses as `None` and
refuses. Adding `UNKNOWN` would create a value that looks like an answer.

### 3.2 `licence` becomes conditional, not optional

```text
rights_basis = NAMED_LICENCE   ->  licence REQUIRED and non-empty
rights_basis = DIRECT_GRANT    ->  licence MUST be absent
```

Both directions are enforced. The second matters as much as the first: a
`DIRECT_GRANT` resource carrying a licence string would be exactly the
fabrication §1 rejects, arriving through a different door.

### 3.3 `basis` — the existing prose field — stays and stays mandatory

`AuthorizedDataset.basis` already holds the justification, and its docstring
gives the reason: *"an authorised dataset with no stated basis cannot be
re-checked against the document that authorised it"*. Under `DIRECT_GRANT` it
carries more weight than before, because it is now the only prose saying **which
grant**. It should quote or cite the granting sentence.

## 4. What must NOT get easier

§15 is the constraint that shapes the whole design: **a `DIRECT_GRANT` must not
satisfy a `NAMED_LICENCE` allowlist.**

World Bank's authorisation genuinely depends on a licence allowlist —
`CC-BY-4.0` and `ODbL-1.0` — because its platform distributes datasets under
several licences and the wrong one carries obligations we have not accepted. If
`DIRECT_GRANT` were allowed to pass that check, the change would have quietly
disabled the one rule that makes World Bank collection safe.

So the allowlist rule becomes:

```text
if scope.licence_allowlist is not None:
    require descriptor.rights_basis is NAMED_LICENCE      # new
    require descriptor.licence in scope.licence_allowlist  # unchanged
```

A `DIRECT_GRANT` descriptor meeting a licence allowlist is **refused**, and the
refusal says why rather than reporting a missing licence — a resource whose
basis is not the kind the scope requires is a different failure from one whose
licence is unrecorded, and a reader chasing the second when it was the first
loses an afternoon.

### 4.1 Fail-closed on absence, unchanged

| Descriptor state | Outcome |
|---|---|
| no `rights_basis` | **refused** — an unestablished basis is not a basis |
| `NAMED_LICENCE`, no licence | **refused** — unchanged from today |
| `NAMED_LICENCE`, licence outside allowlist | **refused** — unchanged |
| `DIRECT_GRANT` meeting a licence allowlist | **refused** — §15, new |
| `DIRECT_GRANT`, scope has no allowlist | allowed, if every other rule passes |

## 5. Backward compatibility

**No stored record changes.** `raw_records.provenance` holds `"licence"` on the
six World Bank rows and none of them is touched — §16 forbids it and there is no
reason to.

**The three existing config entries gain `rights_basis: NAMED_LICENCE`
explicitly.** They are not defaulted into it, and the loader refuses an entry
that omits it.

That is a deliberate rejection of the easier option. Inferring
`NAMED_LICENCE` from the presence of a licence string would work today for all
three, and it would mean a future entry that forgot the field got silently
classified as licensed. §28 requires a missing basis to fail; a default is the
opposite of failing.

Editing three lines of configuration is not "rewriting historical records": the
compliance file is current governance, and the records it authorised are
untouched.

**No database migration.** `AuthorizedDataset` lives in
`source-compliance-v1.json`, not in a table. The only schema artefact is the
contract enum, which is generated.

## 6. What this does not attempt

- **It records a reviewed basis; it does not decide one.** The model has no
  opinion about whether a direct grant is legally sufficient. A reviewer decided
  that when the review was written; this stores which kind of thing they relied
  on. `source-registry-v1.md` §0 — not a legal decision engine — is unchanged.
- **It does not add a third basis for future cases** (public domain, statutory
  exception, negotiated contract). Two values cover every source in the catalog.
  Adding a third when a real source needs one is a contract change with an
  obvious trigger; adding them now would be speculative vocabulary nobody has
  reviewed.
- **It does not touch attribution.** `render_attribution` already handles an
  absent licence identifier — GDELT's obligation does not include one, and that
  is why the omission is safe rather than lucky.

## 7. Summary of the change

| Change | Where |
|---|---|
| `RightsBasis` closed enum, 2 values | `packages/contracts/schema/domain.v1.json`, generated |
| `AuthorizedDataset.rights_basis`, required | `compliance/config.py` |
| `AuthorizedDataset.licence` conditional on the basis | `compliance/config.py` |
| `ResourceDescriptor.rights_basis`, defaults to unestablished | `compliance/resources.py` |
| Licence allowlist requires `NAMED_LICENCE` | `compliance/resources.py` |
| `rights_basis: NAMED_LICENCE` on 3 existing entries | `source-compliance-v1.json` |

**No DB migration. No stored record altered. No source verdict changed.**
