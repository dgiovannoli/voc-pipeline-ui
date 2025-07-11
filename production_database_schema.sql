-- Production Database Schema for VOC Pipeline
-- This schema supports the Stage 3 findings with Buried Wins v4.0 framework

-- ============================================================================
-- STAGE 1: CORE RESPONSES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS stage1_data_responses (
    id BIGSERIAL PRIMARY KEY,
    response_id VARCHAR(255) UNIQUE NOT NULL,
    verbatim_response TEXT NOT NULL,
    subject VARCHAR(500),
    question VARCHAR(500),
    deal_status VARCHAR(100) DEFAULT 'closed won',
    company_name VARCHAR(255),
    interviewee_name VARCHAR(255),
    interview_date DATE,
    file_source VARCHAR(255),
    client_id VARCHAR(100) DEFAULT 'default',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for stage1_data_responses
CREATE INDEX IF NOT EXISTS idx_stage1_client_id ON stage1_data_responses(client_id);
CREATE INDEX IF NOT EXISTS idx_stage1_company ON stage1_data_responses(company_name);
CREATE INDEX IF NOT EXISTS idx_stage1_deal_status ON stage1_data_responses(deal_status);
CREATE INDEX IF NOT EXISTS idx_stage1_interview_date ON stage1_data_responses(interview_date);
CREATE INDEX IF NOT EXISTS idx_stage1_created_at ON stage1_data_responses(created_at);

-- ============================================================================
-- STAGE 2: RESPONSE LABELING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS stage2_response_labeling (
    id BIGSERIAL PRIMARY KEY,
    quote_id VARCHAR(255) NOT NULL,
    criterion VARCHAR(100) NOT NULL,
    relevance_score INTEGER CHECK (relevance_score >= 0 AND relevance_score <= 5),
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed')),
    priority VARCHAR(20) DEFAULT 'medium',
    confidence VARCHAR(20) DEFAULT 'medium',
    relevance_explanation TEXT,
    deal_weighted_score DECIMAL(5,2),
    context_keywords TEXT,
    question_relevance VARCHAR(50) DEFAULT 'unrelated',
    client_id VARCHAR(100) DEFAULT 'default',
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for stage2_response_labeling
CREATE INDEX IF NOT EXISTS idx_stage2_quote_id ON stage2_response_labeling(quote_id);
CREATE INDEX IF NOT EXISTS idx_stage2_criterion ON stage2_response_labeling(criterion);
CREATE INDEX IF NOT EXISTS idx_stage2_relevance_score ON stage2_response_labeling(relevance_score);
CREATE INDEX IF NOT EXISTS idx_stage2_sentiment ON stage2_response_labeling(sentiment);
CREATE INDEX IF NOT EXISTS idx_stage2_client_id ON stage2_response_labeling(client_id);
CREATE INDEX IF NOT EXISTS idx_stage2_analysis_timestamp ON stage2_response_labeling(analysis_timestamp);

-- ============================================================================
-- STAGE 3: FINDINGS TABLE (Production Ready)
-- ============================================================================

CREATE TABLE IF NOT EXISTS stage3_findings (
    id BIGSERIAL PRIMARY KEY,
    finding_id VARCHAR(50) UNIQUE NOT NULL,  -- F1, F2, etc.
    finding_statement TEXT NOT NULL,
    interview_company VARCHAR(255),
    interview_date DATE,
    deal_status VARCHAR(100) DEFAULT 'closed won',
    interviewee_name VARCHAR(255),
    supporting_response_ids TEXT,  -- Comma-separated list
    evidence_strength INTEGER DEFAULT 1,
    finding_category VARCHAR(100),  -- Barrier, Opportunity, Strategic, Functional
    criteria_met INTEGER DEFAULT 0,
    priority_level VARCHAR(50) DEFAULT 'Standard Finding',  -- Priority Finding, Standard Finding
    primary_quote TEXT,
    secondary_quote TEXT,
    quote_attributions TEXT,
    
    -- Buried Wins specific fields
    criterion VARCHAR(100),
    finding_type VARCHAR(100),
    enhanced_confidence DECIMAL(3,1),
    criteria_scores JSONB,  -- Store as JSON for flexibility
    impact_score DECIMAL(5,2),
    companies_affected INTEGER DEFAULT 1,
    quote_count INTEGER DEFAULT 1,
    selected_quotes JSONB,  -- Store as JSON array
    themes JSONB,  -- Store as JSON array
    deal_impacts JSONB,  -- Store as JSON object
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evidence_threshold_met BOOLEAN DEFAULT FALSE,
    evidence_strength_score INTEGER DEFAULT 0,
    criteria_covered TEXT,
    credibility_tier VARCHAR(100),
    title VARCHAR(500),
    description TEXT,
    
    -- Client siloing
    client_id VARCHAR(100) DEFAULT 'default',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for stage3_findings
CREATE INDEX IF NOT EXISTS idx_stage3_finding_id ON stage3_findings(finding_id);
CREATE INDEX IF NOT EXISTS idx_stage3_client_id ON stage3_findings(client_id);
CREATE INDEX IF NOT EXISTS idx_stage3_criterion ON stage3_findings(criterion);
CREATE INDEX IF NOT EXISTS idx_stage3_finding_type ON stage3_findings(finding_type);
CREATE INDEX IF NOT EXISTS idx_stage3_priority_level ON stage3_findings(priority_level);
CREATE INDEX IF NOT EXISTS idx_stage3_enhanced_confidence ON stage3_findings(enhanced_confidence);
CREATE INDEX IF NOT EXISTS idx_stage3_evidence_strength ON stage3_findings(evidence_strength);
CREATE INDEX IF NOT EXISTS idx_stage3_interview_company ON stage3_findings(interview_company);
CREATE INDEX IF NOT EXISTS idx_stage3_interview_date ON stage3_findings(interview_date);
CREATE INDEX IF NOT EXISTS idx_stage3_created_at ON stage3_findings(created_at);

-- GIN indexes for JSON fields
CREATE INDEX IF NOT EXISTS idx_stage3_criteria_scores_gin ON stage3_findings USING GIN (criteria_scores);
CREATE INDEX IF NOT EXISTS idx_stage3_selected_quotes_gin ON stage3_findings USING GIN (selected_quotes);
CREATE INDEX IF NOT EXISTS idx_stage3_themes_gin ON stage3_findings USING GIN (themes);
CREATE INDEX IF NOT EXISTS idx_stage3_deal_impacts_gin ON stage3_findings USING GIN (deal_impacts);

-- ============================================================================
-- STAGE 4: THEMES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS stage4_themes (
    id BIGSERIAL PRIMARY KEY,
    theme_id VARCHAR(100) UNIQUE NOT NULL,
    theme_name VARCHAR(255) NOT NULL,
    theme_description TEXT,
    theme_category VARCHAR(100),
    theme_priority VARCHAR(50),
    theme_confidence DECIMAL(3,1),
    theme_quotes JSONB,  -- Array of quote IDs
    theme_findings JSONB,  -- Array of finding IDs
    theme_insights TEXT,
    theme_recommendations TEXT,
    theme_impact_score DECIMAL(5,2),
    theme_evidence_strength INTEGER,
    theme_companies_affected INTEGER,
    theme_criteria_covered TEXT,
    client_id VARCHAR(100) DEFAULT 'default',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for stage4_themes
CREATE INDEX IF NOT EXISTS idx_stage4_theme_id ON stage4_themes(theme_id);
CREATE INDEX IF NOT EXISTS idx_stage4_client_id ON stage4_themes(client_id);
CREATE INDEX IF NOT EXISTS idx_stage4_theme_category ON stage4_themes(theme_category);
CREATE INDEX IF NOT EXISTS idx_stage4_theme_priority ON stage4_themes(theme_priority);
CREATE INDEX IF NOT EXISTS idx_stage4_theme_confidence ON stage4_themes(theme_confidence);
CREATE INDEX IF NOT EXISTS idx_stage4_created_at ON stage4_themes(created_at);

-- GIN indexes for JSON fields
CREATE INDEX IF NOT EXISTS idx_stage4_theme_quotes_gin ON stage4_themes USING GIN (theme_quotes);
CREATE INDEX IF NOT EXISTS idx_stage4_theme_findings_gin ON stage4_themes USING GIN (theme_findings);

-- ============================================================================
-- PROCESSING METADATA TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS processing_metadata (
    id BIGSERIAL PRIMARY KEY,
    processing_id VARCHAR(100) UNIQUE NOT NULL,
    stage VARCHAR(50) NOT NULL,  -- stage1, stage2, stage3, stage4
    client_id VARCHAR(100) DEFAULT 'default',
    total_records_processed INTEGER DEFAULT 0,
    successful_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    processing_start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_end_time TIMESTAMP WITH TIME ZONE,
    processing_duration_seconds INTEGER,
    processing_status VARCHAR(50) DEFAULT 'running',  -- running, completed, failed
    error_messages TEXT,
    processing_config JSONB,  -- Store processing configuration
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for processing_metadata
CREATE INDEX IF NOT EXISTS idx_metadata_processing_id ON processing_metadata(processing_id);
CREATE INDEX IF NOT EXISTS idx_metadata_client_id ON processing_metadata(client_id);
CREATE INDEX IF NOT EXISTS idx_metadata_stage ON processing_metadata(stage);
CREATE INDEX IF NOT EXISTS idx_metadata_status ON processing_metadata(processing_status);
CREATE INDEX IF NOT EXISTS idx_metadata_start_time ON processing_metadata(processing_start_time);

-- ============================================================================
-- CLIENT CONFIGURATION TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS client_configurations (
    id BIGSERIAL PRIMARY KEY,
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_description TEXT,
    client_settings JSONB,  -- Store client-specific settings
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for client_configurations
CREATE INDEX IF NOT EXISTS idx_client_config_client_id ON client_configurations(client_id);
CREATE INDEX IF NOT EXISTS idx_client_config_active ON client_configurations(is_active);

-- ============================================================================
-- DATA VALIDATION CONSTRAINTS
-- ============================================================================

-- Add constraints to ensure data integrity
ALTER TABLE stage3_findings 
ADD CONSTRAINT chk_enhanced_confidence 
CHECK (enhanced_confidence >= 0 AND enhanced_confidence <= 10);

ALTER TABLE stage3_findings 
ADD CONSTRAINT chk_evidence_strength 
CHECK (evidence_strength >= 0 AND evidence_strength <= 10);

ALTER TABLE stage3_findings 
ADD CONSTRAINT chk_criteria_met 
CHECK (criteria_met >= 0 AND criteria_met <= 10);

ALTER TABLE stage2_response_labeling 
ADD CONSTRAINT chk_relevance_score 
CHECK (relevance_score >= 0 AND relevance_score <= 5);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_stage1_updated_at BEFORE UPDATE ON stage1_data_responses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stage3_updated_at BEFORE UPDATE ON stage3_findings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stage4_updated_at BEFORE UPDATE ON stage4_themes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_client_config_updated_at BEFORE UPDATE ON client_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for high-priority findings
CREATE OR REPLACE VIEW high_priority_findings AS
SELECT 
    finding_id,
    finding_statement,
    interview_company,
    interviewee_name,
    priority_level,
    enhanced_confidence,
    evidence_strength,
    finding_category,
    criteria_met,
    client_id,
    created_at
FROM stage3_findings 
WHERE priority_level = 'Priority Finding' 
AND enhanced_confidence >= 7.0
ORDER BY enhanced_confidence DESC, created_at DESC;

-- View for findings summary by client
CREATE OR REPLACE VIEW findings_summary_by_client AS
SELECT 
    client_id,
    COUNT(*) as total_findings,
    COUNT(CASE WHEN priority_level = 'Priority Finding' THEN 1 END) as priority_findings,
    COUNT(CASE WHEN priority_level = 'Standard Finding' THEN 1 END) as standard_findings,
    AVG(enhanced_confidence) as avg_confidence,
    AVG(evidence_strength) as avg_evidence_strength,
    COUNT(DISTINCT criterion) as criteria_covered,
    COUNT(DISTINCT interview_company) as companies_covered,
    MAX(created_at) as latest_finding_date
FROM stage3_findings 
GROUP BY client_id;

-- View for findings by criterion
CREATE OR REPLACE VIEW findings_by_criterion AS
SELECT 
    criterion,
    COUNT(*) as findings_count,
    AVG(enhanced_confidence) as avg_confidence,
    COUNT(CASE WHEN priority_level = 'Priority Finding' THEN 1 END) as priority_count,
    COUNT(DISTINCT interview_company) as companies_affected,
    MAX(created_at) as latest_finding_date
FROM stage3_findings 
GROUP BY criterion
ORDER BY findings_count DESC;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE stage1_data_responses IS 'Core interview responses and verbatim data from customer interviews';
COMMENT ON TABLE stage2_response_labeling IS 'AI-analyzed quotes with relevance scores, sentiment, and criteria mapping';
COMMENT ON TABLE stage3_findings IS 'Buried Wins v4.0 findings with LLM-generated insights and evidence scoring';
COMMENT ON TABLE stage4_themes IS 'Synthesized themes and patterns across multiple findings';
COMMENT ON TABLE processing_metadata IS 'Processing job metadata and status tracking';
COMMENT ON TABLE client_configurations IS 'Client-specific configurations and settings';

COMMENT ON COLUMN stage3_findings.finding_statement IS 'LLM-generated finding statement following Buried Wins methodology';
COMMENT ON COLUMN stage3_findings.enhanced_confidence IS 'Confidence score (0-10) based on evidence strength and criteria coverage';
COMMENT ON COLUMN stage3_findings.evidence_strength IS 'Evidence strength score (0-10) based on quote quality and quantity';
COMMENT ON COLUMN stage3_findings.criteria_met IS 'Number of Buried Wins criteria met (0-8)';
COMMENT ON COLUMN stage3_findings.criteria_scores IS 'JSON object with individual criteria scores';
COMMENT ON COLUMN stage3_findings.selected_quotes IS 'JSON array of quote objects used as evidence';

-- ============================================================================
-- SAMPLE DATA INSERTION (Optional)
-- ============================================================================

-- Insert default client configuration
INSERT INTO client_configurations (client_id, client_name, client_description, client_settings)
VALUES (
    'default',
    'Default Client',
    'Default client configuration for VOC Pipeline',
    '{"processing_enabled": true, "findings_threshold": 5, "confidence_threshold": 0.5}'
) ON CONFLICT (client_id) DO NOTHING;

-- ============================================================================
-- GRANTS AND PERMISSIONS (Adjust based on your Supabase setup)
-- ============================================================================

-- Grant appropriate permissions (adjust based on your Supabase role setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO authenticated;
-- GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETION
-- ============================================================================

-- Log successful schema creation
DO $$
BEGIN
    RAISE NOTICE 'Production database schema created successfully!';
    RAISE NOTICE 'Tables created: stage1_data_responses, stage2_response_labeling, stage3_findings, stage4_themes, processing_metadata, client_configurations';
    RAISE NOTICE 'Indexes created for optimal query performance';
    RAISE NOTICE 'Views created for common reporting queries';
    RAISE NOTICE 'Triggers created for automatic timestamp updates';
    RAISE NOTICE 'Ready for production deployment!';
END $$; 