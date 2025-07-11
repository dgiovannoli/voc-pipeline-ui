-- Cleanup and fix stage3_findings table structure
-- This script will clean up the table and ensure proper schema

-- First, let's see what columns currently exist
DO $$
BEGIN
    -- Drop the table if it exists and recreate with proper structure
    DROP TABLE IF EXISTS stage3_findings CASCADE;
    
    -- Create the table with proper structure
    CREATE TABLE stage3_findings (
        id SERIAL PRIMARY KEY,
        finding_id VARCHAR(50) UNIQUE NOT NULL,
        finding_statement TEXT NOT NULL,
        interview_company VARCHAR(255),
        interview_date DATE,
        deal_status VARCHAR(100),
        interviewee_name VARCHAR(255),
        supporting_response_ids TEXT,
        evidence_strength INTEGER,
        finding_category VARCHAR(100),
        criteria_met TEXT,
        priority_level VARCHAR(50),
        primary_quote TEXT,
        secondary_quote TEXT,
        quote_attributions TEXT,
        companies_affected JSONB,
        client_id VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Add indexes for performance
    CREATE INDEX IF NOT EXISTS idx_stage3_findings_client_id ON stage3_findings(client_id);
    CREATE INDEX IF NOT EXISTS idx_stage3_findings_finding_id ON stage3_findings(finding_id);
    CREATE INDEX IF NOT EXISTS idx_stage3_findings_company ON stage3_findings(interview_company);
    CREATE INDEX IF NOT EXISTS idx_stage3_findings_date ON stage3_findings(interview_date);
    
    RAISE NOTICE 'stage3_findings table recreated with proper structure';
END $$; 