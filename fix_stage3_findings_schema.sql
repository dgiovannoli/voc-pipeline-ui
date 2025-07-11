-- Fix stage3_findings table schema to allow finding_id to be unique per client
-- Drop the existing unique constraint on finding_id
ALTER TABLE stage3_findings DROP CONSTRAINT IF EXISTS stage3_findings_finding_id_key;

-- Create a composite unique constraint on (client_id, finding_id) instead
-- This allows the same finding_id to exist for different clients
ALTER TABLE stage3_findings ADD CONSTRAINT stage3_findings_client_finding_unique UNIQUE (client_id, finding_id);

-- Add an index on finding_id for better performance
CREATE INDEX IF NOT EXISTS idx_stage3_findings_finding_id ON stage3_findings(finding_id);

-- Add an index on client_id for better performance
CREATE INDEX IF NOT EXISTS idx_stage3_findings_client_id ON stage3_findings(client_id);

-- Add an index on the composite key for better performance
CREATE INDEX IF NOT EXISTS idx_stage3_findings_client_finding ON stage3_findings(client_id, finding_id);

-- Verify the changes
SELECT 
    constraint_name, 
    constraint_type, 
    table_name 
FROM information_schema.table_constraints 
WHERE table_name = 'stage3_findings' 
AND constraint_type = 'UNIQUE'; 