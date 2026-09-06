# Mission 1.74 — Globalping Counterpart Residual Closure V1

**Outcome: `GLOBALPING_TWO_PROVIDER_CLARIFICATIONS_REQUIRED`.** Both residuals were
pursued to the end of the public record. Both narrowed. **Neither closed.** The tally is
unchanged at **10 PASS / 2 PARTIAL / 0 FAIL**, and what the mission produced is two
frozen, hashed, **unsent** questions.

---

## 0. The shape of the finding

Mission 1.73 left two questions and this mission answered neither, which sounds like
nothing happened. What actually happened is that both questions changed from *nobody has
read the documentation* into *the documentation has been read and does not say*.

Those are different states, and the difference decides what comes next. The first is
closed by reading more. The second can only be closed by asking, and that is the whole
reason two enquiry packets exist.

## 1. R1 — everything points the same way and nothing commits the provider

Mission 1.73 checked one surface. This checked **five**, and the specification was
re-verified **on the retrieved bytes rather than on a summary**: 124,793 bytes, **zero**
case-insensitive matches for `redirect`, **zero** for `3xx`, and **byte-identical to the
Mission 1.73 copy**.

The 27 `Location` matches are the API's own asynchronous-measurement header and example
keys such as `pingLocations` — not an HTTP redirect Location. The API repository's two
matches are a package name and an ETag middleware test about the API's own responses; the
CLI's four are OAuth redirect URIs; the website's five are server routing and
trailing-slash middleware. The probe repository has exactly one, in an adoption-server
test.

**So no provider test asserts HTTP measurement redirect behaviour, either way.**

### The statement that points the right way and still does not close it

In the provider's own issue #347 a maintainer writes:

> the body may be empty in some cases, most often redirects and error responses

That **presupposes that a redirect response appears in a Globalping result**, which is
what a non-following apparatus produces. It is real evidence and it is not a contract: it
defines nothing, promises nothing, and appears inside a discussion about `rawOutput`
formatting. Graded `PROVIDER_MAINTAINER_STATEMENT_INCIDENTAL`, and **it did not upgrade
the evidence level**, because closing R1 needs a normative provider contract or a
provider-declared normative implementation, and an incidental premise in an issue about
output formatting is neither — however strongly it points the right way.

**`R1_PARTIAL_IMPLEMENTATION_ONLY` at `R1_C_IMPLEMENTATION_OBSERVED`.**

Three readings were available here and all three are refused in the record. **An
implementation is not a contract.** **A dependency default is not a provider
commitment** — the probe dispatches through `undici.Client.dispatch()`, and undici's
behaviour binds undici. And **zero matches for a word mean the word is absent from a
reviewed surface, never that the behaviour is absent from the apparatus.**

## 2. R2 splits, and only one half closes

### The half that closes, bounded by its own qualifier

The provider asks itself, in the Credits FAQ committed to its own website source:

> Can I use credits to power a commercial tool or product?

and answers:

> Yes, we support commercial use of Globalping within the limits of our terms of service.

**`COMMERCIAL_USE_GENERAL_PERMITTED_WITHIN_TERMS`** — and the qualifier is what bounds
it. *Within the limits of our terms of service* **defers to the Terms for everything
other than commerciality**, so the answer settles WHETHER we may be a commercial user and
says nothing about WHAT we may point the service at. Reading it as third-party-target
permission was the cheap move this mission most had to refuse, and the validator refuses
it too.

It also reconciles the clause Mission 1.73 found: the non-commercial sentence sits under
**"If you are a consumer user:"**, and a provider that markets commercial use is
consistent with a consumer-scoped liability clause once the heading is read.

### The half that does not, and the hook that was followed anyway

§2 Permitted Use reads:

> Globalping works as a platform that allows you to monitor, debug, and benchmark your
> internet infrastructure using a globally distributed network of probes.

**Descriptive in form, under a heading that reads as a limitation.** No *only*, no
*solely*, no prohibition on other purposes — and the two readings are reconciled nowhere.
§5 Prohibited Use enumerates and does not mention third-party measurement, which cuts
toward descriptive; the heading and the word *your* cut the other way.

Then §1 Definitions says *the Globalping platform further described on the Website*, so
**the Terms incorporate the Website's description by reference.** That hook was followed
looking for a widening, and the homepage says *Monitor, debug and benchmark your internet
infrastructure from a globally distributed network of probes.* **The incorporated text
repeats the same narrowing.**

**Following a hook and finding it does not help is a stronger finding than not having
looked.** `THIRD_PARTY_TARGET_SCOPE_UNRESOLVED`.

### Three more readings refused

- The API schema's *A publicly reachable measurement target* is
  `TECHNICAL_TARGET_VALIDATION_ONLY`, because **the provider nowhere states that
  acceptance by the schema is permission under the Terms.**
- The probe README's *We block private IP addresses as targets* presupposes public
  endpoints and is **product design rather than a grant.**
- §3's reservation of *all rights that are not expressly granted* sits in a
  proprietary-rights section about the look and feel of the Website. It is **not** read
  as everything-unmentioned-is-prohibited, and it is **not** ignored either.

## 3. Refusing under ambiguity is governance, not a legal conclusion

`PROVIDER_TERMS_REQUIRE_CLARIFICATION`. The Terms do **not** block the intended activity,
**and that is not the same as permission.**

- **Outcome G (terms block the activity) was available and refused**, because an
  ambiguous Permitted Use section is not an explicit prohibition, and reaching a block
  from ambiguity would convert *nobody has decided* into *the provider has refused*.
- **Outcome H (redirect contract incompatible) was refused** because every signal points
  at not following redirects, which is what the SROS side would want. **What is missing
  is the commitment, not the compatibility.**
- A, B, C, E and F were each refused with their reasons recorded.

## 4. Two enquiries, and why one packet would have been wrong

R1 is a technical contract question about published API behaviour, and the provider
maintains a public issue tracker where maintainers answer such questions. R2 is a Terms
question, and **the Terms themselves designate `legal@globalping.io` in §16.**

**Two provider-designated channels are genuinely required**, so one packet could not have
carried both without sending a Terms question to a technical channel. Each question maps
to exactly one gate; no combined ambiguous question was asked.

Each packet answers to a SHA-256 recomputed over its binding fields, **excluding its own
digest, its send status and its recorded date** — Mission 1.65's envelope rule. Each
records why the public documentation is insufficient and what answer would discriminate
between the closing verdicts.

**`send_status: NOT_AUTHORIZED` on both. `ENQUIRIES_SENT` 0. No operator approval
recorded. No dispatch authorised by this mission.**

## 5. What did not move, and what was not bent

**No PASS dimension was reopened**, because no contradicting evidence was found. C4 was
incidentally reinforced by the same issue that supplied the maintainer statement — the
provider records that `rawOutput` copies `rawHeaders` when the method was HEAD.

ADR-039's HEAD transport route, body retention restriction, source-collection precedence,
robots policy, target exclusions, load limits and run-authorization separation are all
preserved; the GET route is still incompatible with the initial profile; and Mission
1.72's `BODY_PERSISTENCE_DEFAULT` is still `DISABLED`.

**Q1 stays `PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`**, failing on the one condition it
has always failed on. No class selected, `selected-quantity-class-v1.json` still absent,
no construct, **0 independence groups**, `PAIR_ANALYSIS_NOT_READY`.

**The registry is unchanged at 15** for a fourth mission running. Nothing new was observed
that a rule could be written from; reading a provider's Terms carefully is not an
apparatus failure.

## 6. Nothing moved

| | |
|---|---|
| Globalping API executions, measurements created or read, probe runs | 0 |
| target HTTP requests, SROS fetcher runs, target-value exposures | 0 |
| accounts, tokens, trials, purchases, credential reads | 0 |
| mailbox searches, enquiries sent, provider contacts | 0 |
| alternative counterparts evaluated | 0 |
| sources registered, governance mutations, canonical mutations | 0 |
| thresholds, Claims, Evidence, independence groups, reliability values | 0 |
| scores, Opportunity mutations, model calls, embeddings, migrations | 0 |
| constructs selected, quantity classes selected | 0 |

**13 of 18 first-party documentation requests, 2 of which returned nothing usable and are
counted.** ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner
arc still parked.

## 7. Verification

- Validator probed with **207 deliberate violations, 207 caught** — 203 by rule, 4 by
  drift — plus **7 of 7 positive controls, all variants** rather than the shipped bytes.
- **One escape was found, and it was closed by adding a rule rather than by editing a
  record.** The R2 sub-results had no vocabulary of their own, so a bogus value slid past
  a correspondence check that only fired on the good value. A sub-result is now a
  restatement of its review's verdict, and each half of the R2 conjunction must follow its
  own sub-result — which is a stricter rule than the one that leaked.
- The specification was read from the saved bytes rather than from a summary, and the
  byte-identity with the Mission 1.73 copy was checked rather than assumed.
- **116 new tests**; **2738 bare-python tests**; both test runners green; `ruff format --check`, `ruff check` and mypy
  all run through `uv`; all **44** CI gates.

## 8. Next

**The next action is the operator's, and it is not a mission.** Two questions are prepared
and neither may be sent without an explicit authorisation.

- **Do not send either packet** without that authorisation.
- **Do not re-run the public documentation search.** It is exhausted for both questions,
  which is what this mission established.
- **Do not look for an alternative counterpart**, and do not restart quantity-class
  discovery.
- **Do not select a construct** over a route whose request contract is still uncommitted.

**Mission 1.75 was not started.**
