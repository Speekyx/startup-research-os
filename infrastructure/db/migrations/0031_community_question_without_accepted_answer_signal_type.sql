-- =============================================================================
-- 0031 — a seventh signal type, and NO new quantity family
--
-- Mission 1.32, `answer-acceptance-semantics-v1.md`.
-- `community_question_without_accepted_answer_volume`.
--
-- WHY NO NEW FAMILY, unlike ADR-034 one mission earlier. This is still a count
-- of public questions carrying a site tag inside a bounded window; what differs
-- is which questions are counted, not what kind of quantity the count is.
-- `COMMUNITY_QUESTION_VOLUME` already means exactly that, so widening nothing is
-- the correct move and adding a family would have split one quantity across two
-- names. The test is the one ADR-032 and ADR-034 both applied: would the
-- existing family lose its meaning? Here it would not — it would gain a second
-- member that is unmistakably the same kind of thing.
--
-- WHY A SEPARATE TYPE rather than a parameter on the existing one. A signal type
-- carries a SUMMARY that says what the number means, and these two numbers mean
-- different things: 88 questions were filed, and 54 of them had no answer their
-- asker marked accepted. One type with a mode flag would have one summary
-- describing two propositions, and a consumer branching on the type would be
-- unable to tell them apart.
--
-- WHAT THE NAME REFUSES. `unsolved_problem_volume`, `solution_gap_volume`,
-- `dissatisfied_user_volume` and `unmet_demand_volume` were all available and
-- all assert something the source does not. Acceptance is ONE PERSON'S ACTION —
-- only the asker may accept — and the normalizer has said so in the payload
-- since Mission 1.18: "the asker marked an answer accepted; not a statement that
-- the problem is objectively resolved". A field name survives every later
-- caveat, so the name says what the field records and nothing else.
--
-- THIS TYPE MAPS TO NO OPPORTUNITY DIMENSION, decided before it existed. It was
-- tested against SOLUTION_GAP and SOLUTION_DISSATISFACTION and rejected by both;
-- the reasoning is in `answer-acceptance-semantics-v1.md` §0.C and §0.D. Zero
-- dimensions is a real answer (Mission 1.28) and no dimension was invented to
-- give this measurement somewhere to go.
--
-- Forward-only. One registry row, nothing altered, nothing dropped, and a re-run
-- inserts nothing.
-- =============================================================================

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('signal_type', 'community_question_without_accepted_answer_volume',
     'Community questions without an accepted answer',
     'How many public questions carrying one tag from a community site''s own '
     'vocabulary, created inside one bounded window, had NO ACCEPTED ANSWER at the '
     'source state this deployment observed. Acceptance is one person''s action -- '
     'only the asker may accept -- and the state is read whenever the record was '
     'collected, which may be long after the question was written. Says that many '
     'askers had not marked an answer accepted when we looked. Says NOTHING about '
     'whether any problem is solved, whether anyone is dissatisfied, whether existing '
     'tools are adequate, whether a solution gap exists, whether anyone would pay, or '
     'whether any two of the questions concern the same problem. A record carrying no '
     'flag WITHHOLDS the fact and is never counted as unaccepted.')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- What this migration does NOT do.
--
-- No quantity family is added and `signals_quantity_family_check` is untouched:
-- this type declares COMMUNITY_QUESTION_VOLUME, which migration 0030 already
-- admits. No record kind is added — `community_question` has existed since
-- Mission 1.18 and this is the second derivation to read it. No Opportunity
-- dimension is added, deliberately. And nothing downstream is unblocked: a
-- signal of this type produces NON_SCORABLE Evidence like every other, because
-- no reviewed reliability applies to its measurement-by-purpose scope.
-- -----------------------------------------------------------------------------
