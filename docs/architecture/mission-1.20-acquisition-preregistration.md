# Mission 1.20 — Acquisition pre-registration

**Committed BEFORE any question content was read.** Mission 1.20 §6 requires the
acquisition design to be fixed before inspection, and the point of a separate
commit is that git history shows the order rather than the report asserting it.

Nothing below was chosen by looking at Stack Overflow question titles or bodies.
No count query was run to compare candidates: running one would have been
selecting on expected yield, which §4 forbids in its own words.

---

## 1. Governance delta: none

| | |
|---|---|
| Source | `stack-exchange` |
| Profile | `local-private-research-v1` |
| Resource | `questions/stackoverflow` |
| Route | `stack-exchange-api` (Data Dump blocked by name) |
| Collector | `stack-exchange-questions@1.0.0`, unchanged |
| Field selection | the same authorised set and the same API filter |

**Filtering by one tag is inside the authorised resource, and the check is not a
formality.** The review authorised *questions on `stackoverflow`, through the
official API, in bounded queries*. `tagged` is an existing bound on
`StackExchangeBounds` that Mission 1.18 already used with the value `python`, it
reaches the query the source receives, and the compliance entry records no tag
allowlist or restriction of any kind. Changing the VALUE of a query parameter the
review authorised is the same activity on the same resource through the same
route.

**So no review version is opened.** If the acquisition had needed a second site,
a different endpoint, an unlisted field or the Data Dump, that would be a delta
and this mission would stop.

---

## 2. Tool selection, on §4's criteria, before content

Candidates are the three tools for which Mission 1.19 already holds independent
Wikimedia per-item request series: **Kubernetes**, **Docker**, **Podman**.

| Criterion | Kubernetes | Docker | Podman |
|---|---|---|---|
| 1. One clearly identifiable software/tool entity | **no** — a platform of many components (kubectl, controllers, CRDs, cloud distributions) | yes | yes |
| 2. One precise Stack Overflow tag | yes (`kubernetes`) | yes (`docker`) | yes (`podman`) |
| 3. Minimal ambiguity with unrelated meanings | yes | yes — on Stack Overflow the tag means the tool | yes |
| 4. Authorised by the existing resource | yes | yes | yes |
| 5. Enough availability for a bounded sample | yes | yes | **cannot be established without a query** |
| 6. Existing Wikimedia counterpart | `Kubernetes` | `Docker_(software)` | `Podman` |

**Selected: Docker. Stack Overflow tag `docker`. Wikimedia counterpart
`Docker_(software)`.**

**No tie-break was needed**, because the candidates do not satisfy the criteria
equally:

- **Kubernetes fails criterion 1.** §1 asks for one narrowly defined *tool*
  rather than something language-sized, and Kubernetes is a platform whose tag
  spans manifests, controllers, kubectl, Helm and vendor distributions. That is
  a smaller version of the Mission 1.18 mistake, not a fix for it.
- **Podman fails criterion 5, and the failure is honest rather than
  convenient.** It is arguably the narrowest entity of the three. But its
  question volume is low enough that a pre-registered window would be a guess
  with no basis, and §6 forbids extending a window afterwards — so a guess that
  came back with eight questions would produce an S0 that tests nothing.
  Choosing a tool whose sample size cannot be reasoned about in advance is a
  badly designed experiment, not a strict one.
- **Docker satisfies all six**, and is the only candidate that does.

**Stated as a limitation rather than hidden:** the `docker` tag is used on Stack
Overflow for the wider container tooling around the engine — Compose, BuildKit,
Desktop. Docker is one tool more than Kubernetes is and less than Podman is, and
whether that residual breadth defeats the experiment is one of the things the
inspection will show.

**Nothing here rests on expected problem frequency.** Criterion 5 is about
whether a bounded sample can be filled at all, and it is satisfied by choosing
the WINDOW rather than by preferring a busy tool.

---

## 3. The bounds, fixed now

```text
site         stackoverflow          (constant in the collector, not a parameter)
tagged       docker
from_date    2024-03-01
to_date      2024-03-31
page_size    100                    (the API's own documented maximum)
max_pages    2                      (ours; the collector's ceiling is 20)
max_records  200
order/sort   asc / creation         (constants in the collector)
filter       !SyjNl4V)kvv2kw3Qt6    (the same minimising filter, unchanged)
```

**Why this window, and it is not about yield.** March 2024 is the month
containing Mission 1.19's Wikimedia window (2024-03-01 to 2024-03-07) for
`Docker_(software)`. Two corpora about the same entity over an overlapping period
is what makes the future convergence provenance in §5 meaningful at all, and it
is a reason that exists before any question is read.

**Why one month rather than one week.** §6 asks for tens to low hundreds. A week
risks the low tens for a single tag; a month at `page_size` 100 and `max_pages` 2
caps the sample at 200 whatever the underlying volume turns out to be.

**What this pre-registration forbids, for the rest of the mission:**

- no second query, on any tag, in any window;
- no widening of the window because no repeated signature appeared;
- no switch of tool because another looks more promising;
- no collection continued until a repeat appears;
- no relaxation of a signature rule until unrelated failures collapse together.

If the sample yields no defensible repeated signature, that is **outcome S0** and
it is the mission's answer.

---

## 4. What the acquisition may NOT acquire

Unchanged from Mission 1.18 and re-verified on the returned records: `owner` and
every field under it, `last_editor`, `comments`, `answers`, `closed_by`. The
filter excludes them at acquisition, and their arrival is a failure rather than
something to clean up.

**The proposition this mission looks for is REPEATED QUESTION INSTANCES, not
different people reporting one thing.** Without identity, no claim about distinct
reporters may be made, and none will be.
