# The TED egress decision, persisted

Generated from `ted-egress-decision-persistence-v1.json`. Do not edit by hand.

**TED_EGRESS_PERMITTED_WITH_CONDITIONS_AND_ELIGIBILITY_RESTORED**

the approval was verified against the packet rather than trusted, the successor was appended rather than v3 edited, the compliance configuration was re-pointed by performing the re-check rather than by bumping a number, and both human confirmations were re-recorded from the operator's verbatim statement. Every gate now passes and nothing has been sent.

## The append

Review v3 to v4, 18 conditions to 28, 4 required to 5.

the committed catalog was read out of git and compared review by review: 9 reviews before, 10 after, exactly one added, none removed, and zero pre-existing reviews changed by a single byte. No non-review field of ted-eu moved and no other source was touched.

v3's superseded_at moved from null to a timestamp, which is the supersession mechanism rather than an edit. Its assessments, conditions, open questions and evidence rows are untouched, and it still records what it recorded.

**One assessment moved.** `external_model_transmission`, NOT_ASSESSED to PERMITTED_WITH_CONDITIONS. v3 does not DECLARE the field at all. Absent means unasked, and the loader resolves an absent assessment to NOT_ASSESSED, which is what the registry reported.

**The added condition is separate, not a widening.** a SEPARATE condition rather than a widening of ted-database-right-residual-exposure-accepted. That acceptance was written for BOUNDED QUERIES through the authorised acquisition routes, and a transmission to a processor is neither a query nor the same counterparty. Widening an existing human acceptance to cover a new act is what Mission 1.83 refused to do on the operator's behalf, and appending a second condition is what doing it honestly looks like.

## The conditions

| condition | kind | verifier | result |
|---|---|---|---|
| `ted-attribution` | CAPABILITY | capability:source-attribution-display | **SATISFIED** |
| `ted-database-right-residual-exposure-accepted` | HUMAN_CONFIRMATION | local-operator | **SATISFIED** |
| `ted-external-model-transmission-accepted` | HUMAN_CONFIRMATION | local-operator | **SATISFIED** |
| `ted-official-route-only` | CAPABILITY | capability:source-route-binding | **SATISFIED** |
| `ted-personal-data-minimisation` | CAPABILITY | capability:source-field-minimisation | **SATISFIED** |

the operator wrote ONE approval and it covers both: the database-right residual and the onward transmission. Both rows carry it verbatim, and the record says they rest on one act rather than splitting it into two sentences nobody wrote.

## The gates, after

| gate | state |
|---|---|
| source transmission | **PERMITTED_WITH_CONDITIONS** |
| profile egress | PERMITTED_TO_APPROVED_PROVIDERS |
| provider posture | APPROVED |
| eligibility | BLOCKED to **ELIGIBLE** |
| the selected packet | UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS to **AVAILABLE** |

the selected packet's own gate, evaluated in memory over the live standings. AVAILABLE is a permission and not an act: nothing was serialised for a provider, no request was composed and no byte left this machine.

## What did not move

the only rows this mission wrote are governance rows, and they are the point. Every research counter is identical before and after.

Canonical research mutation 0, model calls 0, research-data fetches 0, hypotheses synthesized 0.

## A known consequence, recorded rather than repaired

every TED packet's external_synthesis block in the v4 preparation records UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS with the NOT_ASSESSED reason, which was true when Mission 1.82 wrote it and is no longer the live state.

a historical preparation is never rewritten, which is why v1, v2 and v3 are byte-identical across four missions. The next preparation run writes v5, and it belongs to the mission that needs it rather than to this one. Regenerating in passing would also change 21 packets' blocks as a side effect of a governance act.

**Next: 1.84 Second Opportunity Bounded Synthesis V1.** regenerate the preparation as v5 so the egress blocks describe the live state, then run ONE attended bounded synthesis over the selected packet through the approved route, under a frozen output gate, and persist an Opportunity hypothesis only if that gate accepts it. permission makes synthesis reachable and does not make it correct. The Evidence still establishes market activity, buyer or budget existence and economic value, and still establishes no demand, no willingness to pay and no unmet need.
