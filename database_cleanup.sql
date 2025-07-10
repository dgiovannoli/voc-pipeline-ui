-- Database Cleanup Script
-- Generated automatically - review before running

-- Drop unused column from themes
ALTER TABLE themes DROP COLUMN IF EXISTS fuzzy_match_score;
-- Drop unused column from themes
ALTER TABLE themes DROP COLUMN IF EXISTS semantic_group_id;
-- Drop unused column from themes
ALTER TABLE themes DROP COLUMN IF EXISTS scorecard_theme_id;
-- Drop unused column from themes
ALTER TABLE themes DROP COLUMN IF EXISTS synthesis_theme_id;
-- Drop unused column from stage3_findings
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS scorecard_criterion_priority;
-- Drop unused column from stage3_findings
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS sentiment_alignment_score;