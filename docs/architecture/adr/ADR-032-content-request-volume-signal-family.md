# ADR-032 — A fourth Signal quantity family: `CONTENT_REQUEST_VOLUME`

**Status:** Accepted — Mission 1.19. Amends the Signal taxonomy and contract.
Extends ADR-020 and follows ADR-029's reasoning for a different quantity.

---

## Context

Mission 1.19 added the `content_request_count` record kind (migration 0025): how
many times one named content item was requested on one platform during one
period, by one class of requester. Twenty-one real Wikimedia records exist, all
`VALID`, three articles over seven UTC days.

The Signal contract binds `quantity_family` to the record kind of every
contributing input, through a **one family, one record kind** map. Nothing maps
to `content_request_count`, so a derivation over these records is refused with
`INCOMPATIBLE_INPUT_KINDS` before it begins. The Signal layer cannot express
anything about them at all.

That is the same wall Mission 1.15.9 hit for procurement notices, and it is the
wall working: a family that silently accepted a new record kind would let a
derivation compare quantities nobody established were comparable.

## Decision

Add **`CONTENT_REQUEST_VOLUME`** to `SignalQuantityFamily`, and map it to
`content_request_count`.

Register one signal type under it: **`content_request_change`** — the change in
one item's request count between two ADJACENT periods of one platform's own
publication, under one requester class and one access channel.

### Why not reuse `MEASURED_SERIES`

This was the tempting reuse, and it is the one that had to be argued rather than
assumed, because a request count really is a series in a way a procurement value
never was.

**The family's job is to say which quantities are the same kind of thing.** It
exists so that a GDELT term frequency and a World Bank population figure cannot
be treated as commensurable measurements. `MEASURED_SERIES` means *a quantity a
source reports over a period, carrying a metric and a geography*: a population, a
GDP figure, an unemployment rate. Each is a measurement of a state of the world
that exists whether or not anyone looks.

A content request count is a **count of interactions with a publication**. It
exists only because somebody made a request, it is a property of a platform's
traffic rather than of the world, and it carries no geography and no metric it is
an instance of. Placed in `MEASURED_SERIES`, a pageview change and a population
change would carry the same family, and a later aggregation would have no field
left that says they are not the same kind of quantity.

So the widening would not have cost `metric` its meaning the way ADR-029's would
have. It would have cost the family its meaning, which is worse: the field would
still validate and would no longer discriminate.

### Why not reuse `LEXICAL_FREQUENCY`

Structurally closer than it looks — both count occurrences in a window — and
still wrong. `LEXICAL_FREQUENCY` counts occurrences of a TERM in text a source
processed, and its scope carries the term, the language label and the mapping
state. A request count has no term and no language; it has an ITEM and a
requester class. Reusing it would put an article title where a consumer reads a
term, and would leave the requester class with nowhere to live.

### Why the name says REQUEST and VOLUME

`CONTENT_VIEWS` would put "somebody looked" in the field a consumer branches on.
`CONTENT_POPULARITY` and `CONTENT_ATTENTION` would put an interpretation there.
Wikimedia's own definition is *"a request for content of a page that receives a
response of 200 OK or 304 Not Modified"*, and the family name stays at the level
the source measures.

The same argument ADR-029 made against a `WILLINGNESS_TO_PAY` family: the reading
somebody wants is exactly the one that must not be written into the vocabulary,
because a field name survives every later caveat.

## Consequences

- `nlp.signals.quantity_family` widens its CHECK constraint (migration 0026,
  forward-only: no stored row can become invalid).
- `content_request_change` is registered as a signal type.
- `FACT_RULES` gains `content_request_count` as a supplier of
  `EXACT_NUMERIC_VALUE`, `SOURCE_PERIOD_LABEL`, `SOURCE_RELATIVE_ORDER` and
  `COMPARABLE_INSTANT`. It supplies neither `LEXICAL_TERM` nor
  `CLASSIFIED_GEOGRAPHY` nor `PAIRED_MONETARY_AMOUNT`, so a derivation asking for
  one of those over these records is refused rather than reading a field that is
  not there.
- `SignalScope` gains `content_ids`, `content_platforms`, `audience_classes` and
  `access_channels`. A dimension no input carries has **no key at all**, the rule
  the lexical kind established for geography and ADR-029 followed for currencies.

## What this does not decide

**Nothing about what a request count means.** The family says which quantities
are comparable with which. It does not say that a request is a reader, that a
reader is a user, that a user is a customer, or that any number of them is
interest, demand, adoption, popularity or a market.

**Nothing about confounders.** `content_request_change` is a subtraction between
two adjacent days of one series. Every article-level confounder cancels because
both members are the same article; the calendar does not, and neither do news
events. Those are stated on the signal type and again on any Claim built from it,
and they make an INFERENCE unsound rather than the subtraction untrue.

**Nothing about repeated user problems.** The same ENTITY measured repeatedly is
not the same USER PROBLEM recurring (Mission 1.19 §21). This family supplies the
first and says nothing about the second.
