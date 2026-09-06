-- 0036 — the runtime role can read the use-profile vocabulary
--
-- ONE GRANT. NO DDL, NO DATA, NO COLUMN, NO TABLE.
--
-- Mission 1.75 made `use_profile` a required input on the three source
-- governance routes, and an input that is required has to be VALIDATED against
-- something. The canonical vocabulary is `registry.use_profiles`, created by
-- migration 0021 — which granted SELECT on the view it rebuilt and did not
-- grant it on the table it created. Every other table in `registry` is readable
-- by `sros_app`; this one was the exception, and nothing noticed because until
-- now nothing read it at runtime.
--
-- WHY THE VOCABULARY CANNOT BE RESOLVED FROM WHAT IS ALREADY READABLE. Profile
-- identifiers also appear in `source_eligibility.use_profile_id` and
-- `source_policy_reviews.assessed_use_profile`. Both enumerate the profiles that
-- have BEEN USED, not the profiles that are REGISTERED. Validating against them
-- would refuse a registered profile that no source has been reviewed under yet
-- — which is the state every new profile begins in — and would make the
-- vocabulary a function of review data. A profile would blink into existence
-- when the first review landed and vanish if the last one were superseded.
--
-- WHY NOT A LIST IN PYTHON. Two implementations of one vocabulary is the risk
-- this codebase names elsewhere and answers by comparing rather than trusting.
-- A hard-coded pair in a router would also be exactly the "generic over valid
-- registered profiles" rule inverted: it would work until a third profile were
-- registered, and then fail closed against a profile the registry knows.
--
-- WHAT THIS DOES NOT DO. It grants SELECT and nothing else, on a table holding
-- profile definitions — no research data, no credentials, no personal data. The
-- runtime role remains unable to write anywhere in `registry`, which is the
-- property that keeps source review administered through `sros-source` and not
-- through an HTTP request. No row is inserted, updated or deleted by this
-- migration, so it has no historical-data consequence at all.

GRANT SELECT ON registry.use_profiles TO sros_app;

COMMENT ON TABLE registry.use_profiles IS
    'The canonical use-profile vocabulary. Readable by the runtime role since '
    'Mission 1.75, because the governance routes require an explicit profile and '
    'validate it here rather than against the profiles that happen to have '
    'reviews. Administered through sros-source; the runtime role holds SELECT '
    'only, like everything else in this schema.';
