# Internet-Wide Service Presence — Time Contract V1

**Mission 1.59 — Internet-Wide Service-Presence Route Gate Closure V1 — recorded 2026-09-05. Gate 5.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_service_presence_route.py`.

**How often an apparatus scans is not what the proposition needs. What it needs is whether an observation can be ATTRIBUTED to a defined window before any value is retrieved.**

Two counts are not comparable merely because both are described as daily, weekly, snapshot or current. Cadence is not timestamp identity.

## Apparatus A — Censys — `MERGED_CURRENT_STATE`

- `basis`: Its host-dataset documentation states the queryable dataset is constructed from individual scans and presented as consolidated IP address profiles.
- `per_observation_timestamp_exists`: True
- `per_observation_timestamp_searchable`: False
- `detail`: `observed_at` on a service record marks when the service was obtained by a Censys scan, and its own documentation states that service observation timestamps change too rapidly across indexed services to be published fast enough to allow searching on it. `host.services.scan_time` marks when a service was LAST observed.
- `searchable_time_field`: host-level `last_updated_at`, which reflects the time of the latest CHANGE to host data
- `the_worked_example_that_decides_it`: Censys documentation states that a host with a service observed by a Censys scanner every day for five days WITHOUT CHANGE carries a `last_updated_at` in the searchable index from five days ago. So the searchable time answers when the record last CHANGED, not when the host was last OBSERVED.
- `point_in_time_history_exists`: True
- `point_in_time_history_shape`: per-host timelines preserving a snapshot per scan, with plan-bounded access windows and a compare-two-events view. This is per-host inspection.
- `aggregate_window_selection_documented`: False
- `additional_finding`: Under high service density the documentation states that service data shown represents a SAMPLING of service details, so a record is not necessarily a complete enumeration of that host's services.

## Apparatus B — Netlas — `DISCRETE_POINT_IN_TIME_OBSERVATIONS`

- `basis`: Its responses field reference states that each document represents a single service response collected during scanning, identified by the combination of uri and ip.
- `per_observation_timestamp_exists`: True
- `per_observation_timestamp_searchable`: NOT_ESTABLISHED, but the field is documented
- `detail`: Two temporal fields are documented. `@timestamp` is when the response was indexed, which is a record-processing time. `scan_date` is when the internet-wide scanning activity that generated the captured response occurred.
- `aggregate_window_selection_documented`: the field exists and is documented; whether it is usable as an aggregate filter is not stated
- `what_remains_undefined`: How 'current' data is determined, whether a scan-cycle identifier exists, and whether records are replaced when a service is rescanned.

## The mismatch

**One apparatus publishes a STREAM OF OBSERVATIONS, each carrying the time it was made. The other publishes a MAINTAINED CURRENT STATE, whose searchable time field records when a record last changed. These are not two grains of one thing; they answer different questions.**

Applying a window W to the observation stream selects hosts OBSERVED during W. Applying the searchable time field to the merged state selects hosts whose record CHANGED during W. A host continuously present and unchanged throughout W is in the first set and absent from the second. So the same filter expression picks out two different populations.

Taking 'the current state on both sides' does not produce one time semantic. On the merged side, current membership includes hosts last actually probed at varying and undocumented staleness, governed by a retention and merge policy rather than by an observation window. On the observation side, current is not defined at all in the documentation retrieved.

## Alignment rules evaluated

| rule | verdict | why |
| --- | --- | --- |
| `A_exact_timestamp_equality` | **IMPOSSIBLE** | Two independent scanners on independent schedules do not probe a host at the same instant, and one side's observation time is not searchable in any case. |
| `B_same_protocol_defined_bounded_observation_interval` | **NOT_AVAILABLE** | It is exactly the right rule and it needs both sides to expose observation-time selection. One side documents no aggregate window selector at all. |
| `C_pre_frozen_maximum_timestamp_distance` | **REFUSED** | Section 16. A tolerance needs an operational basis, and none is available: the merged side publishes no bound on how stale a member of the current state may be. A delta chosen without that bound would be a round number dressed as a rule, and it would be chosen precisely because it salvages the route. |
| `D_one_snapshot_inside_the_other_scan_interval` | **REFUSED** | It requires knowing the merged side's scan interval for the specific hosts counted, which is per-host timeline information rather than an aggregate property. Establishing it would mean retrieving the set first and inspecting it afterwards, which is the procedure section 18 forbids. |

## Measurement difference against world change

If the two apparatuses disagree, the disagreement must be attributable either to measurement difference or to world change, and the time rule is what makes that attribution possible.

**Under this pair.** It is not attributable. A host present throughout the window but unchanged is absent from one side's window-filtered set for a reason that is neither a measurement difference nor a change in the world: it is an artefact of what that side's searchable timestamp means. A contradiction produced that way would be an artefact recorded as a finding, which is the worst failure available to this layer.

## Gate 5 — `FAIL`

Rule freezable before values: **False**. Retrospective pairing required: **True**.

**Blocker.** The only procedure that could pair an A observation with a B observation is to retrieve both sets and then inspect per-host timelines to discover which members were actually observed inside the window. Section 18 fails gate 5 for exactly that procedure, because a rule that can only be applied after the values are in hand is not a preregistrable rule.

*Why FAIL rather than UNKNOWN.* This is not a missing document. The named cadence question was pursued and answered: one side documents its per-record scan time, and the other documents that its queryable dataset is a merged current state whose searchable time field records changes rather than observations, with no aggregate window selector. The mismatch is established from first-party documentation on both sides.

*What would change it.* An apparatus A that exposes observation-time selection over an aggregate, or a documented Censys surface that does. Neither is a matter of looking harder at what was read.

## The asymmetry worth carrying forward

**The failure is not a property of the CLASS. It is a property of one apparatus's exposure model.**

Netlas's shape -- discrete observation documents each carrying the time the observation was made -- is exactly what a preregistered threshold proposition needs. Censys's shape is a maintained current-state view, which is an excellent product for asking what is running now and the wrong object for asking what was observed during a window.

**OBSERVATION_ADDRESSABLE_EXPOSURE: an apparatus qualifies only if a future observation can be attributed to a defined window from its published surface, before any value is retrieved.**

