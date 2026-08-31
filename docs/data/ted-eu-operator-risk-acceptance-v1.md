# TED-EU Operator Residual-Risk Acceptance V1

**Authoritative.** Mission 1.15.6.1. The one human decision, recorded.

**State: `AUTHORIZATION_READY`, with two qualifiers stated in §7 and §8.** The
condition `ted-database-right-residual-exposure-accepted` is **SATISFIED**, and
`AcquisitionAuthorizationContext` **builds** for `ted-eu` under
`local-private-research-v1`.

**H-36A remains `NOT ESTABLISHED`. H-36B remains `NOT ADDRESSED`.** No legal
clearance was obtained, claimed or implied. A human decision resolved a
**condition**; it resolved no legal question.

**No collector exists. No TED procurement data has been collected.**

---

## 1. The acknowledgement, verbatim

Supplied by the operator in French, which is the authoritative text. Reproduced
here character for character, and stored the same way in the verification row's
`reason`:

> J’ai lu intégralement `ted-eu-local-official-route-readiness-v1.md` et
> `ted-eu-authorization-bootstrap-v1.md`.
>
> Je comprends que H-36A est `NOT ESTABLISHED` : rien ne détermine actuellement
> si un droit sui generis sur la base TED existe, ni qui pourrait en être
> titulaire.
>
> Je comprends que H-36B est `NOT ADDRESSED` pour l’extraction large du corpus :
> rien n’établit qu’un tel droit, s’il existe, a été accordé ou abandonné.
>
> Je comprends que l’autorisation locale de `ted-eu` est volontairement limitée.
> Elle repose sur la décision 2011/833/UE, la notice légale TED/SIMAP, les
> métadonnées `COM_REUSE` et l’usage publié par l’Office des publications pour
> les routes officielles, et qu’aucun de ces éléments ne constitue à lui seul
> une concession explicite d’un droit de base de données.
>
> Je comprends que cette acceptation repose également sur des requêtes bornées
> et ciblées, sur la minimisation des champs dès l’acquisition et sur l’absence
> de redistribution. Si l’une de ces conditions cesse d’être vraie, cette
> acceptation cesse de s’appliquer.
>
> Je comprends qu’il ne s’agit pas d’une validation juridique, qu’aucun avocat
> n’a validé cette analyse et que cette acceptation ne résout ni H-36A ni H-36B.
>
> J’accepte le risque résiduel et non résolu lié aux droits de base de données
> pour `ted-eu`, uniquement sous `local-private-research-v1`, review version 2,
> et pour rien d’autre.
>
> Cette acceptation ne s’étend pas à `commercial-multi-tenant-research-v1`, à
> une future utilisation publique, vendue, par abonnement, orientée client ou
> multi-tenant, aux packages Bulk XML, au dataset historique `ted-csv`, à une
> autre source ou à une future review TED substantiellement différente.

**Not summarised, not translated in the record, not strengthened.** In
particular this is **not** "TED database rights accepted": the decision is the
acceptance of a **residual, unresolved exposure**, under one profile and one
review version.

**One wording difference, recorded rather than smoothed over.** Item 4 of the
canonical acknowledgement says *none of those four is a database-right grant*;
the operator wrote *aucun de ces éléments ne constitue **à lui seul** une
concession **explicite** d'un droit de base de données*. The operator's hedge is
kept as written. It changes nothing operative — the acceptance clause itself
states the exposure is **résiduel et non résolu**, which is only coherent if
nothing has granted the right — and the record must carry the operator's words
rather than the template's.

## 2. What was recorded

| | |
|---|---|
| Source | `ted-eu` |
| Use profile | `local-private-research-v1` |
| Review version | **2** |
| Condition | `ted-database-right-residual-exposure-accepted` |
| Verification kind | `HUMAN_CONFIRMATION` |
| Result | **`SATISFIED`** |
| Verifier (actor) | `local-operator` |
| Verifier version | `acknowledgement-v1` |
| Recorded at | 2026-08-31T20:09:29Z |
| Reference | this document |
| Rows written | **exactly one** |

`local-operator` is the neutral identifier
[`ted-eu-authorization-bootstrap-v1.md`](ted-eu-authorization-bootstrap-v1.md)
allows where no canonical operator identity exists in the repository. **No real
legal name was invented in governance data.**

`acknowledgement-v1` names **which text was signed**, not a program version. If
§6.2 of the bootstrap document is ever revised, a reader can tell which wording
this decision was recorded against.

**Written through the existing append-only mechanism**
(`registry.source_condition_verifications`, migration 0007) and through nothing
else. **No CLI verb records human confirmations, and none was built** — Mission
1.15.6 refused to build one on the reasoning that a command which records them is
one flag away from a script that records them, and that decision stands. This
row was written by a one-off act that is not part of the repository.

## 3. What it does not mean

**H-36A remains `NOT ESTABLISHED`.** Nothing determines whether a sui generis
database right subsists in the TED corpus, or who would hold it.

**H-36B remains `NOT ADDRESSED`** for broad corpus extraction. Nothing
establishes that such a right, if it subsists, has been granted or waived.

**This is not a legal clearance.** No lawyer reviewed this analysis, and the
operator says so in their own acknowledgement.

The acceptance is a decision to **proceed with unresolved uncertainty** under a
narrow profile. It is not a finding that the uncertainty is gone, and no document
in this repository says otherwise.

## 4. Scope, and what is excluded

The acceptance applies to `ted-eu`, under `local-private-research-v1`, at review
version **2**, and to nothing else. It does not extend to:

`commercial-multi-tenant-research-v1` · any future public, customer-facing,
sold, subscription-based or multi-tenant deployment · the bulk XML packages ·
the `ted-csv` historical dataset · full corpus mirroring · redistribution ·
model training · embeddings · any other source · a materially changed future TED
review.

**Two of those limits are structural rather than promises.**

- **Profile.** The row hangs off a condition, the condition hangs off exactly one
  review, and that review names one `assessed_use_profile`. The commercial review
  carries no such condition, so an acceptance cannot reach it.
  `build_authorization('ted-eu', 'commercial-multi-tenant-research-v1')` still
  refuses with `REQUIRES_REVIEW`, and the refusal does not mention this condition.
- **Review version.** Each review version owns its **own** condition rows
  (`registry.source_review_conditions` is keyed `(review_id, condition_key)`).
  Local v1 and v2 already hold two distinct rows for this key. A future v3 would
  create a third with `satisfied = FALSE`, and this acceptance could not reach it.

## 5. What did not change

| | |
|---|---|
| Routes | `ted-search-api` and `ted-open-data-sparql` authorised; **`ted-bulk-xml` refused by name** and absent from the context |
| Preferred route | `ted-search-api` — an implementation preference, never broader permission |
| Dataset families | `ted-bulk-xml-daily`, `ted-bulk-xml-monthly`, `ted-csv-historical` excluded; an unclassified resource denied |
| Field minimisation | the authorised set permitted; every natural-person field refused, alone and hidden among allowed fields |
| Redistribution | `NOT PERMITTED` |
| Model training | not authorised, on both registered profiles |
| Embeddings | blocked, D-12 open |
| Commercial profile | `REQUIRES_REVIEW` |

**The acceptance granted none of these and could not have.** They are enforced by
the gates Mission 1.15.6 built, not by anything an operator promises.

## 6. The authorization

```text
build_authorization('ted-eu', 'local-private-research-v1')  ->  CONTEXT

  use profile   local-private-research-v1
  review        v2  APPROVED_WITH_CONDITIONS
  routes        ted-open-data-sparql, ted-search-api
  ted-bulk-xml  ABSENT
  preferred     ted-search-api
```

## 7. Qualifier one — the context grants no reachable resource yet

**`resource_ready` is NO.** TED's compliance entry authorises **zero concrete
datasets** (`"datasets": []`), so `context.authorized_dataset(...)` returns
nothing for every resource and `authorize_resource` denies every descriptor for
want of a rights basis and a dataset family.

This is the state Eurostat has been in since Mission 1.4, and the reason Mission
1.9.2 separated `resource_ready` from `eligible`: a source can pass the gate
while every resource it could ask for is refused.

**So the collector mission's first act is not writing a client.** It is
authorising a concrete resource — the eForms contract notices and contract award
notices, from 1 March 2023, through the reviewed routes — with a stated basis,
which is a governance act.

## 8. Qualifier two — the recorded decision and the live verifiers do not meet

**No shipped command produces a complete verification set for a source that has a
human condition**, and this is the finding of the mission rather than a footnote.

| Path | What it sees |
|---|---|
| Live (`verify_source`, and therefore `build_authorization` with no arguments, `sros-source authorization`, `evaluate_readiness`) | the three `CAPABILITY` conditions `SATISFIED`; the human one **`UNKNOWN`, always, by design** |
| Recorded (`registry.source_review_conditions.satisfied`, and the `registry.source_eligibility` SQL view) | the human one **`SATISFIED`**; the three capability ones unrecorded, so `FALSE` |

Neither half is complete, and nothing joins them. The authorization in §6 was
built by supplying the union — which is exactly what `build_authorization`'s
`verifications` parameter exists for — and no production caller does that today.

**And re-verification would erase the acceptance.** Verified empirically, in a
rolled-back transaction:

```text
sros-source --use-profile local-private-research-v1 verify ted-eu --apply

  ted-attribution                                -> SATISFIED
  ted-official-route-only                        -> SATISFIED
  ted-personal-data-minimisation                 -> SATISFIED
  ted-database-right-residual-exposure-accepted  -> UNKNOWN     <-- clears it

  acceptance boolean before : True
  acceptance boolean after  : False
```

`verify_source` yields `UNKNOWN` for a human condition, and
`record_verifications` writes `satisfied = FALSE` for every non-`SATISFIED`
result — correct and deliberate for a capability that stopped holding, and
destructive for a decision a person made once.

**Operational consequence, until this is addressed: do not run
`verify --apply` for `ted-eu` under this profile.** It would revoke the
acceptance silently, and re-recording it would put a second `SATISFIED` row in an
append-only log, making one decision look like two.

**Not fixed here.** How re-verification should treat a human condition is a real
design decision — skip them, preserve them, or require an explicit withdrawal —
and Mission 1.15.6.1 was scoped to record one decision and change no model. It
belongs to the mission that decides it.

## 9. Where this leaves TED

| | |
|---|---|
| Verdict | `APPROVED_WITH_CONDITIONS` under `local-private-research-v1` v2 |
| Conditions | **4 of 4 satisfied**, across the live and recorded halves |
| Authorization context | **builds** |
| `resource_ready` | **no** — no concrete dataset is authorised |
| Collector | **none, and none was written** |
| H-36A · H-36B | **NOT ESTABLISHED · NOT ADDRESSED** |

**Next: Sprint 1 — Mission 1.15.7, TED Official Search API Collector V1 — Local
Private Research Profile**, whose first act is §7's resource authorisation and
which must decide §8 before anything can be relied on twice.

The previous attempt, and why it was refused, is preserved in
[`ted-eu-operator-acceptance-pending-v1.md`](ted-eu-operator-acceptance-pending-v1.md).
