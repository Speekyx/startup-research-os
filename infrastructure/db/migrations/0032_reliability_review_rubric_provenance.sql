-- 0032 — which review procedure produced a reliability value
--
-- Mission 1.42a found RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP: the table records
-- WHAT a reviewer decided, WHO decided it and WHICH documents it rests on, and
-- nothing about the PROCEDURE they followed. Once a rubric exists, that omission
-- means a later reader cannot ask which assessments were made under it.
--
-- Two nullable columns and nothing else. Mission 1.42.1 §2 keeps this narrow on
-- purpose: multi-review persistence, reviewer disagreement and reviewer
-- confidence are all real questions and none of them is this one.
--
-- WHY THE BASIS TABLE WAS NOT USED INSTEAD. A basis row names a retrieved
-- document ABOUT THE MEASUREMENT -- a methodology statement, a field
-- definition, a documented limitation. The rubric is the procedure the reviewer
-- followed, not evidence about the publisher, and filing it there would inflate
-- the documentary basis of every future assessment with a document that says
-- nothing about the source.
--
-- WHY NULLABLE, AND WHY NOTHING IS BACKFILLED. The two assessments that exist
-- today were reviewed before the rubric existed. NULL is the true answer for
-- them, and writing a rubric id onto a review that never used one would
-- fabricate provenance -- the exact failure this column is being added to
-- prevent. A DEFAULT would do the same thing more quietly.

ALTER TABLE epistemic.reliability_assessments
    -- The review procedure, e.g. `human-reliability-assessment-rubric`. NULL
    -- means the review predates any rubric, never that the reviewer skipped one.
    ADD COLUMN review_rubric_id      TEXT,
    -- The exact version, e.g. `1.0.0`. A rubric that changes its dimensions
    -- changes what a value means, so the version is part of the provenance.
    ADD COLUMN review_rubric_version TEXT;

-- Half a provenance is worse than none: an id with no version names a moving
-- target, and a version with no id names nothing at all.
ALTER TABLE epistemic.reliability_assessments
    ADD CONSTRAINT reliability_assessments_rubric_provenance_check
        CHECK (
            (review_rubric_id IS NULL     AND review_rubric_version IS NULL)
         OR (review_rubric_id IS NOT NULL AND review_rubric_version IS NOT NULL)
        );

COMMENT ON COLUMN epistemic.reliability_assessments.review_rubric_id IS
    'The review procedure this judgement was made under. NULL for reviews that '
    'predate any rubric; never backfilled, because a rubric id on a review that '
    'did not use one is fabricated provenance.';

COMMENT ON COLUMN epistemic.reliability_assessments.review_rubric_version IS
    'The exact rubric version. Required with the id and forbidden without it: a '
    'rubric that changes its dimensions changes what a value means.';
