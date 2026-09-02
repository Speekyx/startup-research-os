# Source-Native Issue Identity — Candidate Landscape V1

**Authoritative.** Mission 1.21 §4-§8. Which public defect trackers expose a
publisher-declared canonical-duplicate relation, and which of those can actually
be acquired under `local-private-research-v1`.

**The requirement that decides everything here:** SROS must not decide that two
reports mean the same thing. The SOURCE must already have said so, as issue
state.

---

## 1. The structural gate, applied first

§5 admits a candidate only if its documented data model carries an explicit
source-native identity relation — `dupe_of`, `duplicate_of`, `merged_into` or
equivalent — recorded as **actual issue state**. A "possible duplicate"
suggestion, a similarity endpoint, a shared label or a shared component is
excluded by name.

| Shape | Relation, from first-party API documentation | Passes §5 |
|---|---|---|
| **Bugzilla** | `dupe_of` (int) — *"The bug ID of the bug that this bug is a duplicate of. If this bug isn't a duplicate of any bug, this will be null."* | **yes** |
| **Launchpad** | `duplicate_of_link` (writeable, *"Link to a bug … Duplicate Of"*) and `duplicates_collection_link` (*"MultiJoin of bugs which are dupes of this one"*) | **yes** |
| **Debian BTS** | `merge` / `merged-with` — the maintainer merges reports into one | **yes** |
| **Jira** | `duplicates` / `is duplicated by` issue links | yes, weaker — a link type rather than a field on the issue |
| **GitLab** | closing an issue as a duplicate is a quick action and a system note | **no** — no canonical field in the documented model |
| **GitHub** | `state_reason` records that an issue was closed as a duplicate | **no** — the CLOSE REASON is state; the canonical TARGET is not a documented field. And `github` is `RESTRICTED` and was not reopened (§4) |

**Three shapes pass the structural gate.** That alone answers the question
Mission 1.20 left open: **the explicit-identity route exists.** Whether it is
reachable is a separate question, and it is the one that decided this mission.

---

## 2. Winner — The Document Foundation Bugzilla (LibreOffice)

`https://bugs.documentfoundation.org/rest/`

| | |
|---|---|
| Identity relation | `dupe_of`, a documented Bugzilla REST field |
| Route | official Bugzilla REST API, no authentication, public bugs only |
| Data licence | **CC BY-SA 4.0**, stated by the deployment itself |
| Field allowlist | `include_fields`, documented and **verified working** |
| Identity on the wire | **none**, when the allowlist omits it |

**The licence statement is on the tracker, not on the software, and that
distinction is §11's whole point.** The front page of the deployment states:

> "Please note that all contributions to The Document Foundation Bugzilla are
> considered to be released under the Creative Commons Attribution-ShareAlike
> 4.0 International License, unless otherwise specified."

**TDF states licences per deployment**, which is the strongest available evidence
that this one is meant seriously: the LibreOffice website is CC BY-SA **3.0**,
the TDF Wiki is CC BY-SA **3.0 Unported**, and the Bugzilla is CC BY-SA **4.0**.
Three properties, three separate statements, three different versions. Nobody
copied a footer.

**CC BY-SA 4.0 is an instrument this repository has already read in full**
(Mission 1.18, for Stack Exchange): it grants reproduction and the production of
Adapted Material for any purpose including commercial, subject to attribution and
ShareAlike — and ShareAlike attaches to Adapted Material that is **Shared**,
which `local-private-research-v1` does not do.

**What decided it against the runner-up is a mechanism, not a preference.**
Bugzilla REST documents `include_fields`, and a live probe of this deployment
returned exactly the six requested fields and nothing else:

```json
{"bugs": [{"status": "CLOSED", "dupe_of": null, "product": "LibreOffice",
           "resolution": "FIXED", "component": "LibreOffice", "id": 29381}]}
```

No reporter, no assignee, no CC list, no comments — **absent from the wire, not
filtered afterwards.**

**What the relation does NOT establish:** that the classification is objectively
correct, that two different people reported it, how many users are affected, how
severe it is, whether it is still current, or that anyone would pay to fix it.
It establishes that **the publisher classified one bug as a duplicate of
another.**

---

## 3. Runner-up — Launchpad (Ubuntu and hosted projects)

`https://api.launchpad.net/1.0/`

**Structurally the richest of the three**, and it loses on acquisition
mechanics.

Launchpad exposes the relation in **both directions**: a duplicate carries
`duplicate_of_link`, and the canonical bug carries `duplicates_collection_link`
and `number_of_duplicates`. Nothing else surveyed lets the canonical issue
enumerate its own duplicates.

**Its rights position is genuinely elegant**, and worth recording because it
splits exactly where this mission's minimisation does. From Launchpad's own
policies page, under *Bugs copyright*:

> "All bug comments are the property of the people who created them. Metadata
> and statistics generated by the Launchpad Bug Tracker are the property of
> Canonical Ltd and may be used freely for any purpose as long as accreditation
> and the Launchpad URL are given along with that data."

A positive grant over **exactly the metadata this mission wants**, freely and for
any purpose, with a clear condition — and comments, which this mission does not
want, expressly outside it.

**It loses on §12.** A live probe of `api.launchpad.net/1.0/bugs/1` returned
**41 fields including `owner_link`**, and adding a field allowlist changed
nothing — 41 fields again. Launchpad's API has no field-selection mechanism for
an entry representation.

So acquiring the duplicate relation from Launchpad means **receiving a person
link on every request and discarding it afterwards**, which is the practice this
repository refuses by name: *a request that fetched the owner object and
discarded it has still fetched it, and no method removes a field from a record
already collected* (Mission 1.18 §9).

**Recorded rather than discarded.** If a future mission needs the
canonical-side enumeration Launchpad uniquely offers, the rights evidence is here
and the blocker is named: minimisation at acquisition, not permission.

---

## 4. Third — Mozilla Bugzilla

`https://bugzilla.mozilla.org/rest/`

Same `dupe_of`, same `include_fields`, and by far the largest corpus of the
three. **It loses on §7 criterion 3, legal clarity.**

No first-party document found states a licence for bug content on that
deployment. The Mozilla Websites & Communications Terms of Use say content is

> "generally made available for public sharing and reuse through open licenses
> such as Creative Commons … In most cases we ask Mozilla contributors to release
> Content under open licenses."

**"Generally", "such as" and "in most cases" describe a practice, not a grant**,
and the deployment's own footer links *Legal* without stating a data licence.
Under rule 8 of the source registry contract, that is `NOT_ADDRESSED` and it
blocks — and reading it as a grant would be the over-read that produced three
withdrawn approvals in Mission 1.7.

**Not a criticism of Mozilla and not a permanent verdict.** It is the difference
between a foundation that put a licence line on its tracker and one that did not,
and the second may simply not have been asked.

---

## 5. Also considered, and why not

- **Debian BTS** — `merged-with` is real publisher-declared identity and the
  route is first-party. The Debian WWW Pages License covers `www.debian.org`
  pages; nothing found licenses BTS report content. Same failure as Mozilla.
- **Jira (public deployments)** — `duplicates` is a link type rather than a field
  on the issue, so §5 admits it only weakly; and each public deployment carries
  its own operator's terms, which multiplies the governance work per corpus
  rather than settling it.
- **GitHub** — `RESTRICTED` on retrieved terms, and §4 forbids reopening a
  restricted source because its data model is attractive. No new governing
  evidence was sought and none was found in passing.

---

## 6. What this landscape establishes

**The explicit-identity route is available**, and the winner was decided by two
first-party facts rather than by preference: a licence stated on the deployment
itself, and a field allowlist that works.

**And the runner-up's failure is the more interesting one.** Launchpad grants
more and exposes more, and cannot be minimised at acquisition. A route can be
permitted and still be unusable under a posture, which is the same shape Mission
1.15.6 recorded for TED's bulk XML from the other direction.
