-- Complete Stage 3 Findings Table Schema
-- This script recreates the table with ALL required columns

-- Drop and recreate the table with complete schema
DROP TABLE IF EXISTS stage3_findings CASCADE;

CREATE TABLE stage3_findings (
    -- Primary key and unique identifier
    id SERIAL PRIMARY KEY,
    finding_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Core finding data (Buried Wins format)
    finding_statement TEXT NOT NULL,
    interview_company VARCHAR(255),
    interview_date DATE,
    deal_status VARCHAR(100) DEFAULT 'closed won',
    interviewee_name VARCHAR(255),
    supporting_response_ids TEXT,
    evidence_strength INTEGER DEFAULT 1,
    finding_category VARCHAR(100),
    criteria_met TEXT,
    priority_level VARCHAR(50) DEFAULT 'Standard Finding',
    primary_quote TEXT,
    secondary_quote TEXT,
    quote_attributions TEXT,
    
    -- Enhanced analysis fields
    criterion VARCHAR(100),
    finding_type VARCHAR(100),
    enhanced_confidence DECIMAL(3,1) DEFAULT 0.0,
    criteria_scores JSONB,
    impact_score DECIMAL(5,2) DEFAULT 0.0,
    companies_affected JSONB DEFAULT '1',
    quote_count INTEGER DEFAULT 1,
    selected_quotes JSONB,
    themes JSONB,
    deal_impacts JSONB,
    
    -- Metadata and tracking
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evidence_threshold_met BOOLEAN DEFAULT FALSE,
    evidence_strength_score INTEGER DEFAULT 0,
    criteria_covered TEXT,
    credibility_tier VARCHAR(100),
    title VARCHAR(500),
    description TEXT,
    
    -- Client siloing
    client_id VARCHAR(50) DEFAULT 'default',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_stage3_findings_client_id ON stage3_findings(client_id);
CREATE INDEX idx_stage3_findings_finding_id ON stage3_findings(finding_id);
CREATE INDEX idx_stage3_findings_company ON stage3_findings(interview_company);
CREATE INDEX idx_stage3_findings_date ON stage3_findings(interview_date);
CREATE INDEX idx_stage3_findings_confidence ON stage3_findings(enhanced_confidence);
CREATE INDEX idx_stage3_findings_priority ON stage3_findings(priority_level);

-- Add comments for documentation
COMMENT ON TABLE stage3_findings IS 'Enhanced findings from Stage 3 analysis with Buried Wins framework';
COMMENT ON COLUMN stage3_findings.finding_id IS 'Unique identifier for the finding (e.g., F1, F2)';
COMMENT ON COLUMN stage3_findings.finding_statement IS 'The main finding statement in Buried Wins format';
COMMENT ON COLUMN stage3_findings.criteria_scores IS 'JSON object containing scores for different criteria';
COMMENT ON COLUMN stage3_findings.selected_quotes IS 'JSON array of quotes supporting this finding';
COMMENT ON COLUMN stage3_findings.companies_affected IS 'JSON array of companies affected by this finding';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ stage3_findings table recreated with complete schema';
    RAISE NOTICE '📊 All required columns added for production use';
END $$; 