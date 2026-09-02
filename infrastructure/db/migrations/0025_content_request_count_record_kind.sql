-- =============================================================================
-- 0025 — the content-request-count record kind
--
-- Mission 1.19. ONE registry row and NO schema change, for the reason migrations
-- 0011, 0022 and 0024 record: `acquisition.normalized_records` already carries
-- `payload JSONB` and a `record_kind_id` with a foreign key to
-- `registry.registry_entries`, so the storage exists and what is missing is
-- permission to use it. Without this row every insert naming the kind is
-- refused, and `validate_normalization.py` asserts that the kinds declared in
-- `RECORD_KINDS` are exactly those a migration inserts, so the declaration and
-- the row cannot drift.
--
-- WHY A FIFTH KIND rather than widening one that exists. A page view is a COUNT
-- OF REQUESTS for one named content item, over one period, from one class of
-- requester. It carries no geography, so `numeric_observation` would have to
-- make `geography.source_code` meaningless for it — the same objection that
-- produced the lexical kind in Mission 1.10. It counts requests for a DOCUMENT
-- rather than occurrences of a TERM, so `lexical_frequency_observation` would
-- have to lose the language and the term that give it its meaning, and a
-- consumer reading `term` would find an article title. It is nobody's
-- procurement and nobody's question.
--
-- GENERIC, NOT SOURCE-SPECIFIC. The kind is `content_request_count`, not
-- `wikimedia_pageview`. Any platform that publishes how many times a named item
-- was requested in a period has this shape, and naming the kind after the first
-- source to reach it would make the vocabulary a list of vendors — the rule
-- Mission 1.18 established with `community_question` and the reason it is worth
-- having established once.
--
-- WHY THE NAME SAYS "REQUEST" AND NOT "VIEW". Wikimedia's own definition is 'a
-- request for content of a page that receives a response of 200 OK or 304 Not
-- Modified'. A request is what is counted. "View" implies a person looked,
-- "visit" implies a session, "reader" implies a human, and every one of those
-- would be a step past what the source measures — written into the vocabulary,
-- where nothing downstream could unmake it.
--
-- WHAT THIS ROW IS NOT. A vocabulary entry, not a claim that anything downstream
-- exists. It does not assert that a request is a reader, a user, a customer,
-- interest, curiosity, demand, popularity, adoption or a market. `audience.class`
-- is REQUIRED precisely so that no record can exist without saying which
-- population it counted.
--
-- Forward-only. Reversing it is deleting one row, safe for as long as no
-- normalized record references it.
-- =============================================================================

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('normalization_record_kind', 'content_request_count',
     'Content request count',
     'How many times one named content item was requested on one platform during '
     'one period, by one class of requester. Source data: the platform''s own '
     'item identifier, the period it counted, the requester class it attributed '
     'the traffic to, and the count. It asserts that the platform COUNTED that '
     'many requests, and never that a person read, a reader existed, a user '
     'adopted, a customer bought, or that interest, curiosity, demand, '
     'popularity or a market exists. The requester class is required rather than '
     'optional: the same item on the same day carries a different count for '
     'human-attributed traffic than for all traffic, and a record that did not '
     'say which one it held would be two measurements wearing one name.')
ON CONFLICT (registry, id) DO NOTHING;
