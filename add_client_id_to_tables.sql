-- Add client_id column to all tables for data siloing
-- This ensures each client's data is completely isolated

-- Add client_id to core_responses table
ALTER TABLE core_responses 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to quote_analysis table  
ALTER TABLE quote_analysis 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to findings table
ALTER TABLE findings 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to enhanced_findings table
ALTER TABLE enhanced_findings 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to themes table
ALTER TABLE themes 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to executive_themes table
ALTER TABLE executive_themes 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Add client_id to criteria_scorecard table
ALTER TABLE criteria_scorecard 
ADD COLUMN client_id TEXT DEFAULT 'default';

-- Create indexes for better performance on client_id queries
CREATE INDEX IF NOT EXISTS idx_core_responses_client_id ON core_responses(client_id);
CREATE INDEX IF NOT EXISTS idx_quote_analysis_client_id ON quote_analysis(client_id);
CREATE INDEX IF NOT EXISTS idx_findings_client_id ON findings(client_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_findings_client_id ON enhanced_findings(client_id);
CREATE INDEX IF NOT EXISTS idx_themes_client_id ON themes(client_id);
CREATE INDEX IF NOT EXISTS idx_executive_themes_client_id ON executive_themes(client_id);
CREATE INDEX IF NOT EXISTS idx_criteria_scorecard_client_id ON criteria_scorecard(client_id);

-- Add comments for documentation
COMMENT ON COLUMN core_responses.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN quote_analysis.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN findings.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN enhanced_findings.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN themes.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN executive_themes.client_id IS 'Client identifier for data siloing - each client sees only their own data';
COMMENT ON COLUMN criteria_scorecard.client_id IS 'Client identifier for data siloing - each client sees only their own data'; 