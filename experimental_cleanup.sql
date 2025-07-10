-- Experimental Feature Cleanup SQL
-- Generated automatically - review before running

-- Remove unused columns from themes table
ALTER TABLE themes DROP COLUMN IF EXISTS fuzzy_match_score;
ALTER TABLE themes DROP COLUMN IF EXISTS semantic_group_id;
ALTER TABLE themes DROP COLUMN IF EXISTS scorecard_theme_id;
ALTER TABLE themes DROP COLUMN IF EXISTS synthesis_theme_id;

-- Remove unused columns from enhanced_findings table
ALTER TABLE enhanced_findings DROP COLUMN IF EXISTS scorecard_criterion_priority;
ALTER TABLE enhanced_findings DROP COLUMN IF EXISTS sentiment_alignment_score;

-- Remove experimental tables
DROP TABLE IF EXISTS scorecard_themes;
DROP TABLE IF EXISTS executive_themes;
DROP TABLE IF EXISTS criteria_scorecard;

-- Check for views (run this in Supabase dashboard)
-- SELECT schemaname, viewname FROM pg_views WHERE schemaname = 'public';