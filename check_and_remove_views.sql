-- Check for views that depend on columns we want to remove
SELECT schemaname, viewname, definition 
FROM pg_views 
WHERE schemaname = 'public' 
AND definition LIKE '%fuzzy_match_score%';

-- List all views in the database
SELECT schemaname, viewname 
FROM pg_views 
WHERE schemaname = 'public';

-- Drop views that depend on columns we're removing
DROP VIEW IF EXISTS theme_summary_view CASCADE;
DROP VIEW IF EXISTS stage3_findings_view CASCADE;
DROP VIEW IF EXISTS scorecard_themes_view CASCADE;

-- Now we can safely remove the columns
ALTER TABLE themes DROP COLUMN IF EXISTS fuzzy_match_score;
ALTER TABLE themes DROP COLUMN IF EXISTS semantic_group_id;
ALTER TABLE themes DROP COLUMN IF EXISTS scorecard_theme_id;
ALTER TABLE themes DROP COLUMN IF EXISTS synthesis_theme_id;

-- Remove unused columns from stage3_findings table
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS scorecard_criterion_priority;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS sentiment_alignment_score;

-- Remove experimental tables
DROP TABLE IF EXISTS scorecard_themes;
DROP TABLE IF EXISTS executive_themes;
DROP TABLE IF EXISTS criteria_scorecard;

-- Verify cleanup
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name; 