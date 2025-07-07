-- VOC Pipeline Database Cleanup - Remove Unused Tables
-- This script removes tables that are no longer used in the current codebase

-- ============================================================================
-- TABLES TO DELETE (Unused in Current Codebase)
-- ============================================================================

-- 1. LEGACY TABLES (Replaced by enhanced versions)
-- These were created during development but are no longer used

-- Legacy findings table (replaced by enhanced_findings)
DROP TABLE IF EXISTS findings CASCADE;

-- Legacy trend_analysis table (functionality moved to criteria scorecard)
DROP TABLE IF EXISTS trend_analysis CASCADE;

-- Processing metadata table (replaced by processing_logs)
DROP TABLE IF EXISTS processing_metadata CASCADE;

-- ============================================================================
-- TABLES TO KEEP (Currently Used)
-- ============================================================================

-- ✅ CORE TABLES (Actively Used):
-- - core_responses (Stage 1 output)
-- - quote_analysis (Stage 2 output) 
-- - enhanced_findings (Stage 3 output)
-- - themes (Stage 4 output)
-- - executive_themes (Stage 5 output)
-- - criteria_scorecard (Stage 5 output)

-- ✅ ENHANCEMENT TABLES (Recently Added):
-- - processing_logs (for debugging and monitoring)
-- - data_quality_metrics (for quality tracking)
-- - fuzzy_matching_cache (for performance optimization)

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check which tables still exist after cleanup
SELECT 
    table_name,
    CASE 
        WHEN table_name IN ('core_responses', 'quote_analysis', 'enhanced_findings', 'themes', 'executive_themes', 'criteria_scorecard') THEN 'Core Table'
        WHEN table_name IN ('processing_logs', 'data_quality_metrics', 'fuzzy_matching_cache') THEN 'Enhancement Table'
        ELSE 'Other'
    END as table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
AND table_name NOT LIKE 'pg_%'
ORDER BY table_type, table_name;

-- Count records in remaining tables
SELECT 
    'core_responses' as table_name,
    COUNT(*) as record_count
FROM core_responses
UNION ALL
SELECT 
    'quote_analysis' as table_name,
    COUNT(*) as record_count
FROM quote_analysis
UNION ALL
SELECT 
    'enhanced_findings' as table_name,
    COUNT(*) as record_count
FROM enhanced_findings
UNION ALL
SELECT 
    'themes' as table_name,
    COUNT(*) as record_count
FROM themes
UNION ALL
SELECT 
    'executive_themes' as table_name,
    COUNT(*) as record_count
FROM executive_themes
UNION ALL
SELECT 
    'criteria_scorecard' as table_name,
    COUNT(*) as record_count
FROM criteria_scorecard
ORDER BY table_name;

-- ============================================================================
-- CLEANUP SUMMARY
-- ============================================================================

-- Tables Removed:
-- ✅ findings (replaced by enhanced_findings)
-- ✅ trend_analysis (functionality in criteria_scorecard)
-- ✅ processing_metadata (replaced by processing_logs)

-- Tables Kept:
-- ✅ core_responses (Stage 1)
-- ✅ quote_analysis (Stage 2) 
-- ✅ enhanced_findings (Stage 3)
-- ✅ themes (Stage 4)
-- ✅ executive_themes (Stage 5)
-- ✅ criteria_scorecard (Stage 5)
-- ✅ processing_logs (debugging)
-- ✅ data_quality_metrics (quality tracking)
-- ✅ fuzzy_matching_cache (performance)

SELECT 'Database cleanup completed successfully!' as status; 