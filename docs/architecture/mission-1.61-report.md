# Mission 1.61 — Anchor Lineage Confirmation & Partner Documentation Recovery V1

**Outcome: `ANCHOR_LINEAGE_CONFIRMED_OPERATIONAL_QUESTIONS_REMAIN`**, with
`PARTNER_DOCUMENTATION_RECOVERED` beside it. No pair selected, nothing acquired.

---

## 0. The sentence was there

Four missions recorded A7 as PARTIAL because the documentation did not
affirmatively state that no external measurement feed is load-bearing. It states
it. Two retrievals of one page, the second asking for the wording verbatim rather
than in summary:

> All the data is collected independently by Netlas itself. We do not rely on
> third parties or aggregators — every record is obtained and indexed directly by
> the platform.

> The only exceptions are the threat intelligence data shown in the IP/Domain
> Info tool and the geolocation data, which are provided by Netlas partners.

**What makes that LEVEL 2 rather than LEVEL 1 is the second sentence.** An
affirmative claim with an open remainder cannot be checked. An affirmative claim
naming *the only exceptions* can be, and each was: a reputation annotation about
an address is not the presence of a service on it, and where an address sits is
not whether it answered on a port. Neither touches the predicate, so the gate
passes.

**The standard did not move.** It is the same requirement that refused an absence
four missions running. What changed is the document.

## 1. Baseline

Verified live, no drift: 325 / 325 / 33 records, 44 Claims, 45 revisions, 58
Evidence, 1 INFERRED Claim, 1 threshold, 1 derivation, 0 refusals, `SUPPORTS 57 /
CONTRADICTS 1`, 0 Claims carrying both, head `0035`, main `c8d0444`.

## 2. The gate table

```
A1 PASS   A2 PASS*   A3 PASS   A4 PASS   A5 PASS_WITH_STATED_BOUNDS
A6 PASS   A7 PASS    A8 PARTIAL           A9 PASS

blocks  ["A8"]        previously  ["A7", "A8"]
individually qualifies  false
```

`*` A2's pass now carries a bound. See §4.

**Still not qualified, and that is one PARTIAL rather than a formality.** The
gate set is conjunctive, and the unanswered question inside A8 is sampling —
`SAMPLING_IS_LOAD_BEARING` says two apparatuses cannot be compared as one count
unless both expose the same population definition.

## 3. Eleven operational questions, four answered

Two answers are worth more than their status suggests.

**Port 22 is explicitly on the current scanned list.** Mission 1.60 recorded its
inclusion as *not established*. It is established now.

**One record is one service response, not one host.** Record identity combines
the request target and the address, so a host exposing several services yields
several records — which means the construct's count must be a **distinct count
over the address field and never a row count**. A row count would silently
over-count multi-service hosts, and nothing would have reported it.

Unanswered: sampling, failure semantics, vantage.

## 4. A bound on a gate that already passed

The apparatus's **default** search surface is a maintained current-state view.
Its own documentation:

> When a subnet is fully scanned, it automatically 'replaces' the previous
> version in the default output, ensuring the latest complete coverage is always
> prioritized.

> The best option is to search without specifying a particular index. This allows
> you to access the most recently collected complete portion of data.

That is `MAINTAINED_CURRENT_STATE_LAST_CHANGE` — the exact temporal object
Mission 1.59 dropped a pair over.

**A2 still passes**, because the gate asks whether a window is selectable in the
request, and the dated index mechanism is documented and selectable. But the pass
rests entirely on the non-default path. **A collector using the default surface
would be reading the rejected temporal object while a record elsewhere said the
gate had passed**, which is the worst failure available to this layer. The bound
is written into the gate table rather than into a footnote.

## 5. Vantage, and why it is asked now

`NOT_ESTABLISHED` → `NOT_DOCUMENTED`. Three pages and the response schema were
consulted; there is no scanner count, no locations, and **no record field
identifies a scanner node or probe origin** — so vantage could not be established
after the fact even by inspecting retrieved data.

It is asked before pairing because it is where `FRAME_INSIDE_THE_DEFINITION`
would recur: if each apparatus measures the hosts reachable from its own network,
the frame has moved inside the metric, and any proposition admitting both becomes
a disjunction of two vantages.

## 6. Port 22 gives two answers

| | |
|---|---|
| current inclusion | `ESTABLISHED` |
| window addressability | `PORT_22_NOT_ESTABLISHED` |

The changelog dates the **size** of the port list — one entry doubling it, a
later one taking it past a thousand — and never its **membership**. So the list
as of any past date is not reconstructable.

No removal is recorded anywhere. That is favourable evidence about direction and
**not a guarantee**: an absence of recorded removals is an absence, and reading a
positive claim out of a negative space is what this arc has refused four times.

## 7. The partner wall was the path

All three candidates recovered, each earlier failure with a named cause:

| candidate | why Mission 1.60 failed |
|---|---|
| Shadowserver | documentation moved twice, ending on a wiki its own site redirects to |
| ONYPHE | documentation lives on a search subdomain, not the marketing domain |
| LeakIX | the path tried was one level too deep |

Four of eighteen B-slots established, five partial, nine unread. **None is
qualified, ranked or selected.**

**The contrast that paid for a registry rule.** One candidate states its data
comes from daily internet-wide scans, sinkholes, honeypot sensors, sandboxes,
blocklists *and many other sources*. That is affirmative, confident, and LEVEL 1
— a list that does not end cannot be checked against anything. Reading the
anchor's closed clause and that open one in the same mission is what made the
difference legible.

Two precise blockers recorded for the next mission: one candidate's API is
described as mostly private to vetted subscribers, which would make every other
gate moot; another documents that after 30 days it removes *some fields* and
truncates retained raw responses, which would end protocol-native exposure at 30
days if the banner is among them.

## 8. The preference this record declines to express

One candidate emerged with a documented multi-continent vantage, a documented
weekly frame and a published retention table — more than the anchor publishes
about itself on two of those three.

Recording that as a lead would be selecting a partner on a first documentation
pass in which two rivals had pages that did not load. The record names the
temptation instead, so a later reader can audit the refusal rather than detect it.

## 9. The enquiry

Seven questions, one per unresolved point. **Drafted, not sent.**

```
sha256  310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4
```

The hash lives in the closure record, not in the enquiry — writing a hash into
the document it is a hash of changes the bytes it was frozen at. The validator
recomputes it on every run, so a later edit turns the gate red rather than
leaving an approval beside a document nobody approved.

**Nothing already documented is asked**: the validator refuses a question whose
topic the operational record marks `ANSWERED`. It requests no data, no access, no
trial and no price. **No recipient address is recorded** — none was retrieved
first-party, and inventing one would fabricate a fact about the apparatus.

## 10. The validator caught my own record

The forbidden-ask scan refused the enquiry's own sentence saying it asks for *no
trial, no evaluation account, no demo and no quotation*. `testing-strategy.md`
§23, for the sixth time in this repository.

The fix scopes the scan to the text that would actually be **transmitted** rather
than weakening the rule — which is also stricter, since the sendable body is the
only place those phrases could do harm.

## 11. Two requirements added, registry now eleven

| requirement | from |
|---|---|
| `ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE` | 1.61 |
| `LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS` | 1.61 |

The second is the one most easily lost. That every record was self-collected says
nothing about which addresses were reached, and the strongest lineage clause in
this arc sits beside a frame whose sampling is undocumented.

**Mission 1.60's records were not rewritten.** They still read
`ANCHOR_B_LINEAGE_PARTIAL` blocking A7 and A8, which is what that mission found.

## 12. What did not happen

```
queries executed        0        trials started    0
target counts           0        purchases         0
host records            0        facets            0
first-party retrievals  16 of 20   (anchor 7 of 8, partners 9 of 12)
enquiries sent          0
```

0 canonical mutations, 0 sources registered, 0 governance reviews, 0 collectors,
0 threshold registrations, 0 Claims, 0 Evidence, 0 reliability values, 0
independence groups, 0 Scores, 0 Opportunity changes, 0 model calls, 0
embeddings. The Mission 1.56 Claim is untouched.

## 13. Verification

| | |
|---|---|
| CI gates | 29, all green |
| bare-python | 1592 tests across 9 packages |
| pytest | all suites passed across 9 packages |
| database after the pytest run | unchanged across 29 tenant tables and 17 global tables |
| validator probe | 101 deliberate violations, 101 caught |

## 14. Next

**Mission 1.62 — Anchor Operational Closure & Partner Package Completion V1.**
One gate blocks the anchor and one written enquiry answers it. Fourteen of
eighteen partner B-slots are unread, and this mission named which pages hold
them.

It must not fetch a value, execute a query, start a trial, purchase access, read
the anchor's default surface as its addressable one, treat the lineage statement
as a coverage claim, or select a pair before the partner packages are complete.
