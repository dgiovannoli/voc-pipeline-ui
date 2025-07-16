-- Complete Stage 3 Findings Schema with JSONB Support
-- This schema supports JSON-based findings data for better flexibility

-- Drop existing table if it exists
DROP TABLE IF EXISTS stage3_findings;

-- Create stage3_findings table with JSONB columns
CREATE TABLE stage3_findings (
    id SERIAL PRIMARY KEY,
    finding_id VARCHAR(255) UNIQUE NOT NULL,
    finding_statement TEXT NOT NULL,
    finding_category VARCHAR(100),
    impact_score DECIMAL(3,2),
    confidence_score DECIMAL(3,2),
    supporting_quotes JSONB, -- Array of quote strings
    companies_mentioned JSONB, -- Array of company names
    interview_company VARCHAR(255),
    interview_date DATE,
    interview_type VARCHAR(100),
    interviewer_name VARCHAR(255),
    interviewee_role VARCHAR(255),
    interviewee_company VARCHAR(255),
    finding_data JSONB, -- Complete finding data as JSON
    metadata JSONB, -- Additional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_stage3_findings_company ON stage3_findings(interview_company);
CREATE INDEX idx_stage3_findings_category ON stage3_findings(finding_category);
CREATE INDEX idx_stage3_findings_date ON stage3_findings(interview_date);
CREATE INDEX idx_stage3_findings_impact ON stage3_findings(impact_score);
CREATE INDEX idx_stage3_findings_jsonb ON stage3_findings USING GIN(finding_data);
CREATE INDEX idx_stage3_findings_quotes ON stage3_findings USING GIN(supporting_quotes);
CREATE INDEX idx_stage3_findings_companies ON stage3_findings USING GIN(companies_mentioned);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_stage3_findings_updated_at 
    BEFORE UPDATE ON stage3_findings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE stage3_findings IS 'Stage 3 findings with JSONB support for flexible data storage';
COMMENT ON COLUMN stage3_findings.finding_data IS 'Complete finding data as JSON object';
COMMENT ON COLUMN stage3_findings.supporting_quotes IS 'Array of supporting quote strings as JSONB';
COMMENT ON COLUMN stage3_findings.companies_mentioned IS 'Array of mentioned company names as JSONB';
COMMENT ON COLUMN stage3_findings.metadata IS 'Additional metadata as JSON object'; 