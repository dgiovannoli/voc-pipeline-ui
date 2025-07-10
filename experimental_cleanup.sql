-- Experimental Feature Cleanup SQL
-- Generated automatically - review before running

-- First, check for views that depend on columns we want to remove
SELECT schemaname, viewname, definition 
FROM pg_views 
WHERE schemaname = 'public' 
AND definition LIKE '%fuzzy_match_score%';

-- List all views in the database
SELECT schemaname, viewname 
FROM pg_views 
WHERE schemaname = 'public';

-- Drop ALL views that might depend on columns or tables we're removing
-- Use CASCADE to handle any dependencies automatically
DROP VIEW IF EXISTS theme_summary_view CASCADE;
DROP VIEW IF EXISTS stage3_findings_view CASCADE;
DROP VIEW IF EXISTS scorecard_stage4_themes_view CASCADE;
DROP VIEW IF EXISTS scorecard_theme_summary_view CASCADE;
DROP VIEW IF EXISTS executive_stage4_themes_view CASCADE;
DROP VIEW IF EXISTS criteria_scorecard_view CASCADE;

-- Now we can safely remove the columns
-- Remove unused columns from stage4_themes table
ALTER TABLE stage4_themes DROP COLUMN IF EXISTS fuzzy_match_score;
ALTER TABLE stage4_themes DROP COLUMN IF EXISTS semantic_group_id;
ALTER TABLE stage4_themes DROP COLUMN IF EXISTS scorecard_theme_id;
ALTER TABLE stage4_themes DROP COLUMN IF EXISTS synthesis_theme_id;

-- Remove unused columns from stage3_findings table
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS scorecard_criterion_priority;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS sentiment_alignment_score;

-- Remove experimental tables (use CASCADE to handle any remaining dependencies)
DROP TABLE IF EXISTS scorecard_stage4_themes CASCADE;
DROP TABLE IF EXISTS executive_stage4_themes CASCADE;
DROP TABLE IF EXISTS criteria_scorecard CASCADE;

-- Verify cleanup - show remaining tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Show remaining views (should be empty or minimal)
SELECT schemaname, viewname 
FROM pg_views 
WHERE schemaname = 'public';