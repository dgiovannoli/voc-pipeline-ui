-- VOC Pipeline Database Schema Improvements (PostgreSQL Compatible)
-- This script addresses issues encountered during development and testing

-- ============================================================================
-- 1. ADD MISSING COLUMNS TO THEMES TABLE
-- ============================================================================

-- Add missing columns that Stage 4 is trying to use
ALTER TABLE themes 
ADD COLUMN IF NOT EXISTS criteria_covered TEXT[] DEFAULT ARRAY[]::TEXT[];

ALTER TABLE themes 
ADD COLUMN IF NOT EXISTS pattern_type VARCHAR(50) DEFAULT 'criterion_based';

-- Add quotes column for storing contributing quotes (as JSONB)
ALTER TABLE themes 
ADD COLUMN IF NOT EXISTS quotes JSONB DEFAULT '[]'::jsonb;

-- Add fuzzy matching metadata
ALTER TABLE themes 
ADD COLUMN IF NOT EXISTS fuzzy_match_score DECIMAL(3,2);

-- Add semantic grouping metadata
ALTER TABLE themes 
ADD COLUMN IF NOT EXISTS semantic_group_id VARCHAR(50);

-- Add processing metadata
ALTER TABLE themes 
ADD COLUMN IF NOT EXISTS processing_metadata JSONB DEFAULT '{}'::jsonb;

-- ============================================================================
-- 2. ADD MISSING COLUMNS TO ENHANCED_FINDINGS TABLE
-- ============================================================================

-- Add credibility tier column for Stage 3 enhanced findings
ALTER TABLE stage3_findings 
ADD COLUMN IF NOT EXISTS credibility_tier VARCHAR(50) DEFAULT 'Unclassified';

-- Add evidence threshold tracking
ALTER TABLE stage3_findings 
ADD COLUMN IF NOT EXISTS evidence_threshold_met BOOLEAN DEFAULT FALSE;

-- Add quote recycling prevention tracking
ALTER TABLE stage3_findings 
ADD COLUMN IF NOT EXISTS quote_ids_used TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Add processing metadata
ALTER TABLE stage3_findings 
ADD COLUMN IF NOT EXISTS processing_metadata JSONB DEFAULT '{}'::jsonb;

-- ============================================================================
-- 3. ADD MISSING COLUMNS TO CORE_RESPONSES TABLE
-- ============================================================================

-- Add processing status tracking
ALTER TABLE stage1_data_responses 
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending';

-- Add processing timestamp
ALTER TABLE stage1_data_responses 
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE;

-- Add file source tracking
ALTER TABLE stage1_data_responses 
ADD COLUMN IF NOT EXISTS source_file VARCHAR(255);

-- Add chunk information for debugging
ALTER TABLE stage1_data_responses 
ADD COLUMN IF NOT EXISTS chunk_info JSONB DEFAULT '{}'::jsonb;

-- ============================================================================
-- 4. ADD MISSING COLUMNS TO QUOTE_ANALYSIS TABLE
-- ============================================================================

-- Add processing metadata
ALTER TABLE stage2_response_labeling 
ADD COLUMN IF NOT EXISTS processing_metadata JSONB DEFAULT '{}'::jsonb;

-- Add analysis version tracking
ALTER TABLE stage2_response_labeling 
ADD COLUMN IF NOT EXISTS analysis_version VARCHAR(20) DEFAULT '1.0';

-- ============================================================================
-- 5. CREATE NEW TABLES FOR ENHANCED FUNCTIONALITY
-- ============================================================================

-- Create processing_logs table for better debugging
CREATE TABLE IF NOT EXISTS processing_logs (
    id SERIAL PRIMARY KEY,
    stage VARCHAR(50) NOT NULL,
    client_id TEXT NOT NULL,
    operation VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create data_quality_metrics table
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    stage VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    metric_description TEXT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create fuzzy_matching_cache table for performance
CREATE TABLE IF NOT EXISTS fuzzy_matching_cache (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    original_text TEXT NOT NULL,
    matched_text TEXT NOT NULL,
    similarity_score DECIMAL(3,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 6. CREATE INDEXES FOR BETTER PERFORMANCE
-- ============================================================================

-- Indexes for themes table
CREATE INDEX IF NOT EXISTS idx_themes_criteria_covered ON themes USING GIN(criteria_covered);
CREATE INDEX IF NOT EXISTS idx_themes_pattern_type ON themes(pattern_type);
CREATE INDEX IF NOT EXISTS idx_themes_fuzzy_score ON themes(fuzzy_match_score DESC);
CREATE INDEX IF NOT EXISTS idx_themes_semantic_group ON themes(semantic_group_id);
CREATE INDEX IF NOT EXISTS idx_themes_quotes ON themes USING GIN(quotes);

-- Indexes for stage3_findings table
CREATE INDEX IF NOT EXISTS idx_stage3_findings_credibility ON stage3_findings(credibility_tier);
CREATE INDEX IF NOT EXISTS idx_stage3_findings_evidence ON stage3_findings(evidence_threshold_met);
CREATE INDEX IF NOT EXISTS idx_stage3_findings_quote_ids ON stage3_findings USING GIN(quote_ids_used);

-- Indexes for stage1_data_responses table
CREATE INDEX IF NOT EXISTS idx_stage1_data_responses_status ON stage1_data_responses(processing_status);
CREATE INDEX IF NOT EXISTS idx_stage1_data_responses_processed ON stage1_data_responses(processed_at);
CREATE INDEX IF NOT EXISTS idx_stage1_data_responses_source ON stage1_data_responses(source_file);

-- Indexes for stage2_response_labeling table
CREATE INDEX IF NOT EXISTS idx_stage2_response_labeling_version ON stage2_response_labeling(analysis_version);

-- Indexes for new tables
CREATE INDEX IF NOT EXISTS idx_processing_logs_stage_client ON processing_logs(stage, client_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_created ON processing_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_data_quality_client_stage ON data_quality_metrics(client_id, stage);
CREATE INDEX IF NOT EXISTS idx_fuzzy_cache_hash ON fuzzy_matching_cache(text_hash);
CREATE INDEX IF NOT EXISTS idx_fuzzy_cache_client ON fuzzy_matching_cache(client_id);

-- ============================================================================
-- 7. ADD CONSTRAINTS FOR DATA INTEGRITY
-- ============================================================================

-- Add check constraints for data validation (PostgreSQL compatible)
-- Note: These constraints will fail if they already exist, which is fine for this script

-- Add pattern_type constraint
ALTER TABLE themes 
ADD CONSTRAINT check_pattern_type 
CHECK (pattern_type IN ('criterion_based', 'semantic_group', 'cross_criteria'));

-- Add credibility_tier constraint  
ALTER TABLE stage3_findings 
ADD CONSTRAINT check_credibility_tier 
CHECK (credibility_tier IN ('Credible', 'Unclassified', 'Low Evidence'));

-- Add processing_status constraint
ALTER TABLE stage1_data_responses 
ADD CONSTRAINT check_processing_status 
CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'));

-- ============================================================================
-- 8. ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON COLUMN themes.criteria_covered IS 'Array of criteria covered by this theme (for cross-criteria themes)';
COMMENT ON COLUMN themes.pattern_type IS 'Type of pattern: criterion_based, semantic_group, cross_criteria';
COMMENT ON COLUMN themes.quotes IS 'JSONB array of quotes contributing to this theme';
COMMENT ON COLUMN themes.fuzzy_match_score IS 'Similarity score from fuzzy matching (0-1)';
COMMENT ON COLUMN themes.semantic_group_id IS 'ID of semantic group this theme belongs to';
COMMENT ON COLUMN themes.processing_metadata IS 'Additional metadata from theme generation process';

COMMENT ON COLUMN stage3_findings.credibility_tier IS 'Credibility classification: Credible, Unclassified, Low Evidence';
COMMENT ON COLUMN stage3_findings.evidence_threshold_met IS 'Whether this finding meets minimum evidence requirements';
COMMENT ON COLUMN stage3_findings.quote_ids_used IS 'Array of quote IDs used to prevent recycling';
COMMENT ON COLUMN stage3_findings.processing_metadata IS 'Additional metadata from finding generation process';

COMMENT ON COLUMN stage1_data_responses.processing_status IS 'Current processing status of this response';
COMMENT ON COLUMN stage1_data_responses.processed_at IS 'Timestamp when processing completed';
COMMENT ON COLUMN stage1_data_responses.source_file IS 'Original file this response came from';
COMMENT ON COLUMN stage1_data_responses.chunk_info IS 'Information about chunking process';

COMMENT ON TABLE processing_logs IS 'Logs of all processing operations for debugging and monitoring';
COMMENT ON TABLE data_quality_metrics IS 'Quality metrics tracked across all processing stages';
COMMENT ON TABLE fuzzy_matching_cache IS 'Cache for fuzzy matching results to improve performance';

-- ============================================================================
-- 9. CREATE VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for theme summary with enhanced metadata
CREATE OR REPLACE VIEW theme_summary_view AS
SELECT 
    t.id,
    t.theme_statement,
    t.theme_category,
    t.theme_strength,
    t.pattern_type,
    t.criteria_covered,
    t.fuzzy_match_score,
    t.company_count,
    t.finding_count,
    t.avg_confidence_score,
    t.competitive_flag,
    t.client_id,
    t.created_at
FROM themes t
ORDER BY t.created_at DESC;

-- View for enhanced findings with credibility info
CREATE OR REPLACE VIEW stage3_findings_view AS
SELECT 
    ef.id,
    ef.criterion,
    ef.finding_type,
    ef.priority_level,
    ef.credibility_tier,
    ef.title,
    ef.enhanced_confidence,
    ef.criteria_met,
    ef.evidence_threshold_met,
    ef.companies_affected,
    ef.quote_count,
    ef.client_id,
    ef.created_at
FROM stage3_findings ef
ORDER BY ef.created_at DESC;

-- View for processing status overview
CREATE OR REPLACE VIEW processing_status_view AS
SELECT 
    client_id,
    processing_status,
    COUNT(*) as count,
    MIN(created_at) as earliest,
    MAX(created_at) as latest
FROM stage1_data_responses
GROUP BY client_id, processing_status
ORDER BY client_id, processing_status;

-- ============================================================================
-- 10. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to update processing status
CREATE OR REPLACE FUNCTION update_processing_status(
    p_client_id TEXT,
    p_stage TEXT,
    p_status TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO processing_logs (stage, client_id, operation, status, message)
    VALUES (p_stage, p_client_id, 'status_update', p_status, 'Processing status updated');
END;
$$ LANGUAGE plpgsql;

-- Function to get theme statistics
CREATE OR REPLACE FUNCTION get_theme_statistics(p_client_id TEXT)
RETURNS TABLE(
    total_themes BIGINT,
    criterion_based BIGINT,
    semantic_groups BIGINT,
    cross_criteria BIGINT,
    avg_confidence DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_themes,
        COUNT(*) FILTER (WHERE pattern_type = 'criterion_based') as criterion_based,
        COUNT(*) FILTER (WHERE pattern_type = 'semantic_group') as semantic_groups,
        COUNT(*) FILTER (WHERE pattern_type = 'cross_criteria') as cross_criteria,
        AVG(avg_confidence_score) as avg_confidence
    FROM themes 
    WHERE client_id = p_client_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 11. FINAL SUMMARY
-- ============================================================================

-- Display summary of changes
SELECT 'Database schema improvements completed successfully!' as status; 