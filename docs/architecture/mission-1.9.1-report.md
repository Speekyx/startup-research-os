# Mission 1.9.1 — H-28 closed, H-27 still blocked on a network this environment does not have

**Date:** 2026-08-30
**Branch:** `sprint-1/mission-1.9.1`
**Status:** **Partially complete.** H-28 is fully resolved. H-27 is not, and
§36 says stop rather than fabricate — so no fixture was written.

**Deliverables:**
[`acquisition-rights-basis-gap-analysis-v1.md`](../data/acquisition-rights-basis-gap-analysis-v1.md) ·
[ADR-018](adr/ADR-018-acquisition-rights-basis.md) ·
[`gdelt-response-contract-v1.md`](../data/gdelt-response-contract-v1.md) ·
[`gdelt-resource-model-v1.md`](../data/gdelt-resource-model-v1.md) ·
`capture_gdelt_fixtures.py` · `test_rights_basis.py`

---

## 1. H-27 result — blocked, and not for want of trying

Sixteen attempts across two routes, over two missions:

| Target | Result |
|---|---|
| `api.worldbank.org` — the control | **HTTP 200**, same client, moments apart |
| `api.gdeltproject.org/api/v2/doc/doc` | `ConnectTimeout` |
| `api.gdeltproject.org/` | `ConnectTimeout`, then `ECONNREFUSED` |
| proxied route (worked once in Mission 1.9) | `ECONNRESET`, then `HTTP 429` |

GDELT also **does not publish the JSON schema**. Its announcement documents the
parameters and each mode's semantics and states that JSON output exists, without
listing field names. Two independent walls, either sufficient on its own.

Per §5, **nothing was done to work around it**: no proxy intended to bypass, no
rotated identity, no undocumented mirror, no shortened pause against a 429.

## 2. Fixture capture method

`infrastructure/scripts/capture_gdelt_fixtures.py` — ready to run from any
environment that can reach the host.

```bash
python infrastructure/scripts/capture_gdelt_fixtures.py            # capture
python infrastructure/scripts/capture_gdelt_fixtures.py --dry-run  # print only
```

Two requests, fifteen seconds apart, one host, explicit timeouts, redirects not
followed. It opens no database connection and imports no persistence code — the
outputs are test fixtures establishing an external contract, never RawRecords.

It writes response **bytes verbatim** plus a sidecar carrying endpoint, mode,
parameters, capture time, HTTP status, content type, byte length and a
**sha256 of the bytes** — §7 forbids hashing a re-serialised representation,
which would prove only that the reconstruction is stable.

Run here, it fails cleanly, writes nothing, and says so:

```text
FAIL  TimelineTone: ConnectError
      This environment cannot reach GDELT. Run this script from one that can;
      do NOT work around the block (Mission 1.9.1 §5).

2 capture(s) failed. H-27 stays open.
Do not hand-write the fixtures: Mission 1.9.1 §36 says stop instead.
```

## 3. TimelineTone contract — NOT established

Unknown: the container key, the series structure, the timestamp representation,
the tone value representation, whether query metadata is echoed.

**Documented semantics only:** *"instead of coverage volume it displays the
average 'tone' of all matching coverage, from extremely negative to extremely
positive."*

## 4. TimelineVolRaw contract — NOT established

Unknown: the count field name, `norm`'s exact placement, the bucket
representation.

**Documented semantics:** *"the actual number of articles per time interval that
matched the query"*, with `norm` recording the total monitored.

## 5. First supported mode — TimelineTone, provisionally

On the evidence available: tone over time maps onto the committed minimisation
profile *exactly* — `tone_score` plus `observation_period` — and returns no
publisher content.

**Provisional because the fixture has not confirmed it.** §11: if the observed
response cannot be represented within the authorised categories, it is not
forced and the blocker is documented instead.

`ArtList` remains out of scope (§10), and Mission 1.9's finding stands: its
fields are publisher references and headline text.

## 6. TimelineVolRaw governance decision — documented, NOT authorised

One documented fact changes the picture from Mission 1.9, and it is worth being
precise about.

**`MAXRECORDS` is ignored in timeline modes** — GDELT: *"This option only applies
to the ArticleList and various ImageCollage modes."* Mission 1.9 rejected
counting `ArtList` results because the cap made the count a measurement of our
own request bound. **A timeline count is not subject to that cap and is GDELT's
own measurement.** The objection that killed the `ArtList` workaround does not
apply here.

**It is still not authorised.** The committed minimisation profile has no
category for a coverage count, and `norm` is another. Authorising it needs a
reviewed addition to the profile — governance work of the kind Mission 1.8 did.

§12 permits the first collector to support `TimelineTone` only, and it should.
Adding the category *while* writing the collector would be the collector
widening its own permissions.

## 7. H-28 gap analysis

`AuthorizedDataset` required a non-empty `licence`. GDELT grants use directly:

> all datasets released by the GDELT Project are available for unlimited and
> unrestricted use for any academic, commercial or governmental use of any kind
> without fee

A broader grant than most licences give, and not a licence. Every way of filling
the field is a different lie:

| Value | What it asserts | Why false |
|---|---|---|
| `"OTHER"` | a licence of an unenumerated kind | there is no licence |
| `"GDELT Terms Licence"` | GDELT publishes an instrument by that name | **it does not** — the string would be this repository's invention presented as the source's |
| `"NONE"` | unlicensed | it is *permitted*, the opposite of what a reader takes from `NONE` |
| `"N/A"` | the question does not apply | it applies and has an answer |

All of them put an answer to *which licence?* where the real answer is *that is
the wrong question for this source* — and the string reaches every authorised
record's provenance, indistinguishable from `CC-BY-4.0`.

## 8. Rights-basis architecture

`RightsBasis = NAMED_LICENCE | DIRECT_GRANT`, a closed contract enum (ADR-018).

```text
NAMED_LICENCE  ->  licence REQUIRED and non-empty
DIRECT_GRANT   ->  licence MUST be absent
```

**Both directions enforced.** Requiring only "a named licence needs a name"
would leave every fabrication above writable under a direct grant.

**No `UNKNOWN` member**, deliberately asymmetric with `ResourceContentOrigin`.
"Who owns this?" has a genuine third state; "what authorises this?" does not —
an unestablished basis is the *absence* of one, expressed as `None` and refused.
A member spelled `UNKNOWN` would look like an answer.

### 8.1 The allowlist got stricter, not looser

§15 was the constraint that shaped everything:

```python
if scope.licence_allowlist is not None:
    require descriptor.rights_basis is NAMED_LICENCE   # new
    require descriptor.licence in scope.licence_allowlist
```

Before this change a descriptor carrying a licence string and **no basis at all**
passed World Bank's allowlist. Now it does not. A `DIRECT_GRANT` is refused with
a distinct message from a missing licence — the two call for different fixes,
and a reader chasing the wrong one loses an afternoon.

## 9. Backward compatibility

**No database migration. No stored record altered.** `AuthorizedDataset` lives
in `source-compliance-v1.json`; the only schema artefact is the generated
contract enum.

The three existing datasets gained `rights_basis: NAMED_LICENCE` **explicitly**.
Inferring it from the presence of a licence would have avoided editing them and
would have silently mis-classified the first entry that omitted the field — §28
requires a missing basis to fail, and a default is the opposite of failing.

Two internal call sites needed the basis threaded through, and both are worth
noting because each would have been a silent failure:

- **`world_bank.py`** builds descriptors *from* the authorised dataset, so it
  carries `rights_basis=dataset.rights_basis`. Without it every World Bank
  resource would have failed its own allowlist.
- **`capabilities.py`'s probe baseline** builds a synthetic descriptor to prove
  the licence filter both admits and denies. It now carries the basis the scope
  requires — the control case has to pass for the reason it is testing.

Both surfaced as test failures, which is how they should surface.

## 10. GDELT resource model — specified, not committed

[`gdelt-resource-model-v1.md`](../data/gdelt-resource-model-v1.md) carries the
entry in full, ready to commit once the fixture confirms the mode.

Not committed because what a GDELT resource *is* depends on which mode the
collector uses, which is H-27. Committing it now would guess.

### 10.1 Content origin, stated carefully

A tone average is **GDELT's own computation** over its index —
`PLATFORM_LICENSED`. The articles it summarises are the publishers' —
`THIRD_PARTY`, refused, and excluded by the minimisation profile.

An aggregate *about* third-party material is not third-party material, and that
distinction is doing real work rather than being a formality.
`third_party_denied` stays on.

## 11. Resource authorization

| Case | Outcome |
|---|---|
| World Bank, `NAMED_LICENCE` + allowed licence | **allowed** — the control |
| World Bank, `DIRECT_GRANT` | **refused** — §15 |
| World Bank, `DIRECT_GRANT` carrying a licence | **refused** |
| World Bank, no basis | **refused** |
| World Bank, licence outside the allowlist | refused, unchanged |
| GDELT, any resource | **refused** — `datasets` is empty, H-27 |
| ArtList, publisher content, `THIRD_PARTY`, `UNKNOWN`, cross-source | refused, unchanged |

## 12. Identity and query semantics

```text
gdelt | doc-api/timeline-tone | <canonical query> | <bucket start + resolution>
```

**The query is ours**, not a source-native series id, and §21 requires that be
said rather than disguised. Two research questions phrased differently produce
different keys for the same coverage.

The resolution must travel with the bucket start: GDELT picks the step from the
span — 15-minute under 72 hours, hourly to a week, daily beyond — so a bucket
start alone is ambiguous.

**Canonicalisation is syntactic only** (§22): whitespace and parameter encoding,
so transport differences do not fork an identity. No LLM rewrites a query;
claiming two phrasings mean the same thing is a semantic judgment nothing here
is entitled to make.

## 13. Pacing

`rate_limit_known` stays **false**. The 429 proves throttling exists without
revealing its shape, and §23 forbids recording an observed request count as an
official quota.

No runtime pacing was built — there is no collector to pace. The capture script
models the posture instead: two requests, fifteen seconds apart, and a 429 met by
stopping rather than by shortening the pause.

## 14. Tests

**`test_rights_basis.py`, 25 tests.** The ones that matter:

- a `DIRECT_GRANT` is refused by a licence allowlist, with a message distinct
  from a missing licence
- six fabrication strings, each refused under `DIRECT_GRANT`
- a missing basis in config fails; an unknown basis fails
- the control: a `NAMED_LICENCE` resource still passes — a check that only ever
  denies would pass against a gate that denies everything
- the World Bank collector carries the basis into the descriptor it builds

**Three Mission 1.4 tests failed and were corrected rather than relaxed.** Each
built a descriptor with a licence and no basis, which used to pass. They now
state `NAMED_LICENCE`, which is what each always meant — including
`test_an_unknown_licence_fails_closed`, which would otherwise have passed on the
*basis* rule while claiming to test the *licence* rule.

## 15. CI

**CI never runs the capture script and never contacts GDELT.** Availability of a
third party must not decide whether the build passes. Once fixtures are
committed, CI parses those.

## 16. Existing-data survival

Six raw and six normalized World Bank records, verified field by field: values
identical to Mission 1.6.1, `source_id` `world-bank` only, every session link
intact. Registry and tenant state unchanged across the full suite. **Zero GDELT
records.**

## 17. Remaining blockers

**H-27**, and it is the only thing standing between here and Mission 1.9.2. The
tool exists; it needs a network this environment does not have.

**H-28 is closed.** Unchanged: D-03, D-08, D-10, D-12, H-12, H-13, H-22 to H-26,
PROFILE-NOT-CALIBRATED.

## 18. Mission 1.9.2 readiness

**Not yet.** Everything except the fixtures is ready: the rights model holds a
direct grant, the resource entry is written, the host allowlist resolves, the
transport and authorization machinery are unchanged and proven.

The next action is not code. Run one script from a machine that can reach
`api.gdeltproject.org`, commit four files.

---

## The questions §37 asks explicitly

| Question | Answer |
|---|---|
| Were genuine TimelineTone and TimelineVolRaw responses captured? | **No.** H-27 remains open |
| From what environment? | None. This one cannot reach GDELT; the control host returns 200 from the same client |
| Were any fixtures fabricated? | **No.** §36 says stop instead, and nothing was written |
| What is the exact TimelineTone JSON envelope? | **Unknown.** Semantics documented, field names are not published |
| What is the exact TimelineVolRaw JSON envelope? | **Unknown.** Same |
| Which mode should the first collector use? | **TimelineTone**, provisionally — it maps onto the authorised categories exactly. To be confirmed against the fixture |
| Is TimelineVolRaw authorized now? | **No.** Its count is a real GDELT measurement — `MAXRECORDS` is ignored in timeline modes — but the minimisation profile has no category for it. A reviewed addition, not a collector decision |
| How is GDELT's direct grant represented? | `RightsBasis.DIRECT_GRANT`, with the licence field **required to be absent** |
| Was any fake licence introduced? | **No**, and six candidate strings are asserted refused |
| Do named-licence allowlists remain strict? | **Stricter.** They now require the basis *and* the identifier; a descriptor with no basis used to pass |
| Does GDELT have at least one authorized concrete resource? | **No.** The entry is specified and not committed — what a resource *is* depends on the mode, which depends on H-27 |
| Is ArtList still refused? | **Yes** |
| Is publisher content still refused? | **Yes** — excluded by name, and `third_party_denied` unchanged |
| Is GDELT collector-eligible? | **Yes**, unchanged. `APPROVED_WITH_CONDITIONS`, condition satisfied |
| Is a GDELT collector implemented? | **No.** `IMPLEMENTED_COLLECTORS == {"world-bank"}` |
| Is GDELT enabled? | **No** |
| Were any GDELT research records persisted? | **No.** Zero |
| Did World Bank data survive unchanged? | **Yes**, verified field by field |
| Is Mission 1.9.2 safe to begin? | **Not yet** — it needs the fixtures. Everything else is ready |

### Against §36's success criteria

**Criteria 1, 2, 4 and 7 are not met** — the two contracts were not captured, so
the mode choice is provisional and no resource is committed.

**Criteria 3, 5, 6, 8, 9, 10, 11 and 12 are met**: no schema was invented, the
direct grant is represented without a fake licence, named-licence restrictions
are stricter than before, ArtList and publisher content remain refused, GDELT is
unimplemented and disabled, zero research records were persisted, and CI needs
no live GDELT access.

**The mission is half done, and the half that is done is the half that was
hard.** H-28 was a modelling problem with several tempting wrong answers. H-27
is a network this environment does not have.

---

## Validation

Full suite green · registry and tenant state unchanged · ruff check + format ·
mypy strict · contract generation `--check` (RightsBasis generated into both
runtimes) · `validate_schema` · `validate_source_registry` ·
`validate_compliance_capabilities` · `validate_evidence_aggregation` ·
`validate_normalization` · all generated documents in sync · six raw and six
normalized World Bank records unchanged · **zero GDELT records, zero signals,
zero embeddings, zero claims**.
