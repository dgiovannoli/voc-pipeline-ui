-- Drop and recreate stage3_findings table to match CSV structure exactly
DROP TABLE IF EXISTS stage3_findings CASCADE;

CREATE TABLE stage3_findings (
    -- Primary key and metadata
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- CSV fields in exact order
    finding_id TEXT NOT NULL,
    finding_statement TEXT NOT NULL,
    interview_company TEXT,
    date TEXT,
    deal_status TEXT,
    interviewee_name TEXT,
    supporting_response_ids TEXT,
    evidence_strength INTEGER,
    finding_category TEXT,
    criteria_met TEXT,
    priority_level TEXT,
    primary_quote TEXT,
    secondary_quote TEXT,
    quote_attributions TEXT,
    column_1 TEXT,
    column_2 TEXT,
    column_3 TEXT,
    column_4 TEXT,
    column_5 TEXT,
    column_6 TEXT,
    column_7 TEXT,
    column_8 TEXT,
    column_9 TEXT,
    column_10 TEXT,
    column_11 TEXT,
    column_12 TEXT,
    
    -- Additional metadata fields for internal use
    enhanced_confidence NUMERIC(3,1),
    criteria_scores JSONB,
    credibility_tier TEXT,
    companies_affected JSONB,
    processing_metadata JSONB
);

-- Create indexes for performance
CREATE INDEX idx_stage3_findings_client_id ON stage3_findings(client_id);
CREATE INDEX idx_stage3_findings_finding_id ON stage3_findings(finding_id);
CREATE INDEX idx_stage3_findings_priority_level ON stage3_findings(priority_level);
CREATE INDEX idx_stage3_findings_created_at ON stage3_findings(created_at);

-- Create composite unique constraint for client_id + finding_id
ALTER TABLE stage3_findings ADD CONSTRAINT stage3_findings_client_finding_unique UNIQUE (client_id, finding_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_stage3_findings_updated_at 
    BEFORE UPDATE ON stage3_findings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE stage3_findings IS 'Stage 3 findings table matching CSV structure exactly';
COMMENT ON COLUMN stage3_findings.finding_id IS 'Unique finding identifier (e.g., F1, F2)';
COMMENT ON COLUMN stage3_findings.finding_statement IS 'The main finding statement';
COMMENT ON COLUMN stage3_findings.interview_company IS 'Company name from interview';
COMMENT ON COLUMN stage3_findings.date IS 'Date in MM/DD/YYYY format';
COMMENT ON COLUMN stage3_findings.deal_status IS 'Deal status (e.g., closed won)';
COMMENT ON COLUMN stage3_findings.interviewee_name IS 'Name of interviewee';
COMMENT ON COLUMN stage3_findings.supporting_response_ids IS 'Comma-separated response IDs';
COMMENT ON COLUMN stage3_findings.evidence_strength IS 'Number of supporting quotes';
COMMENT ON COLUMN stage3_findings.finding_category IS 'Category (Barrier, Opportunity, etc.)';
COMMENT ON COLUMN stage3_findings.criteria_met IS 'Comma-separated criteria met';
COMMENT ON COLUMN stage3_findings.priority_level IS 'Priority level (Priority Finding, Standard Finding, etc.)';
COMMENT ON COLUMN stage3_findings.primary_quote IS 'Primary supporting quote';
COMMENT ON COLUMN stage3_findings.secondary_quote IS 'Secondary supporting quote';
COMMENT ON COLUMN stage3_findings.quote_attributions IS 'Quote attributions with speaker names'; 