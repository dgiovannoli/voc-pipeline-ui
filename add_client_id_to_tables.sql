-- Add client_id column to all tables for data siloing
-- This ensures each client's data is completely isolated

-- Add client_id to stage1_data_responses table
ALTER TABLE stage1_data_responses 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to stage2_response_labeling table  
ALTER TABLE stage2_response_labeling 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to findings table
ALTER TABLE findings 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to stage3_findings table
ALTER TABLE stage3_findings 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to stage4_themes table
ALTER TABLE stage4_themes 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to executive_stage4_themes table
ALTER TABLE executive_stage4_themes 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to criteria_scorecard table
ALTER TABLE criteria_scorecard 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Create indexes for better performance on client_id queries
CREATE INDEX IF NOT EXISTS idx_stage1_data_responses_client_id ON stage1_data_responses(client_id);
CREATE INDEX IF NOT EXISTS idx_stage2_response_labeling_client_id ON stage2_response_labeling(client_id);
CREATE INDEX IF NOT EXISTS idx_findings_client_id ON findings(client_id);
CREATE INDEX IF NOT EXISTS idx_stage3_findings_client_id ON stage3_findings(client_id);
CREATE INDEX IF NOT EXISTS idx_stage4_themes_client_id ON stage4_themes(client_id);
CREATE INDEX IF NOT EXISTS idx_executive_stage4_themes_client_id ON executive_stage4_themes(client_id);
CREATE INDEX IF NOT EXISTS idx_criteria_scorecard_client_id ON criteria_scorecard(client_id);

-- Add comments for documentation
COMMENT ON COLUMN stage1_data_responses.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN stage2_response_labeling.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN findings.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN stage3_findings.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN stage4_themes.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN executive_stage4_themes.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN criteria_scorecard.client_id IS 'Client identifier for data siloing - each client sees only their own data'; 