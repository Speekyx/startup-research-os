-- =============================================================================
-- 0024 — the community-question record kind
--
-- Mission 1.18. ONE registry row and NO schema change, for the reason migrations
-- 0011 and 0022 record: `acquisition.normalized_records` already carries
-- `payload JSONB` and a `record_kind_id` with a foreign key to
-- `registry.registry_entries`, so the storage exists and what is missing is
-- permission to use it. Without this row every insert naming the kind is
-- refused, and `validate_normalization.py` asserts that the kinds declared in
-- `RECORD_KINDS` are exactly those a migration inserts, so the declaration and
-- the row cannot drift.
--
-- WHY A FOURTH KIND rather than widening one that exists. A community question
-- is a DOCUMENT a person wrote asking how to accomplish or fix something. It
-- carries no measured value, so `numeric_observation` would have to make
-- `observation.value_state` meaningless for it; it counts no term, so
-- `lexical_frequency_observation` would have to lose its term and its language;
-- and it is nobody's procurement, so `procurement_notice` would have to make
-- monetary amounts optional and give a question a buyer. Each of those is the
-- existing kind getting worse for a new source's sake, which is the failure the
-- registry exists to prevent (`normalized-record-v1.md` §5.1).
--
-- GENERIC, NOT SOURCE-SPECIFIC. The kind is `community_question`, not
-- `stack_exchange_question`. A question asked on a public Q&A site is a shape
-- other sources share, and naming the kind after the first source to reach it
-- would make the vocabulary a list of vendors. The SITE is a field; the source
-- is provenance.
--
-- WHAT THIS ROW IS NOT. A vocabulary entry, not a claim that anything downstream
-- exists. It does not assert that a question is a pain, a need, a demand, a
-- market signal or an opportunity. One question is one observation that somebody
-- asked something publicly, and the accepted-answer flag says only that the
-- asker marked an answer accepted -- never that the problem is objectively
-- solved.
--
-- Forward-only. Reversing it is deleting one row, safe for as long as no
-- normalized record references it.
-- =============================================================================

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('normalization_record_kind', 'community_question',
     'Community question',
     'One public question a person asked on a community Q&A site, as the site '
     'published it. Source data: a title, the question text as the site stores '
     'it, the site''s own tags, its creation instant, and the answer metadata '
     'the site exposes. The tags are the SITE''s vocabulary and are never '
     'translated into a taxonomy of ours; an accepted answer means only that '
     'the asker marked one accepted, never that the problem is solved, the '
     'answer is good, or anyone paid for it. Author identity is deliberately '
     'absent: a question is observed, its author is not. A normalized question '
     'supports the claim that the site PUBLISHED a request for help, and never '
     'that a market, a demand, a willingness to pay or an opportunity exists.')
ON CONFLICT (registry, id) DO NOTHING;
