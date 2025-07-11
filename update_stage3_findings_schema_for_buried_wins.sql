-- Update stage3_findings table to match Buried Wins Finding Product Standard
-- This adds the required fields for the Impact -> Evidence -> Context structure

-- First, add the new columns required by the Buried Wins standard
ALTER TABLE stage3_findings 
ADD COLUMN IF NOT EXISTS impact_statement TEXT,
ADD COLUMN IF NOT EXISTS evidence_specification TEXT,
ADD COLUMN IF NOT EXISTS strategic_context TEXT,
ADD COLUMN IF NOT EXISTS score_justification TEXT,
ADD COLUMN IF NOT EXISTS total_score INTEGER,
ADD COLUMN IF NOT EXISTS novelty_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS tension_contrast_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS materiality_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS actionability_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS specificity_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS metric_quantification_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS finding_level VARCHAR(20) DEFAULT 'standard',
ADD COLUMN IF NOT EXISTS source_response_ids TEXT[],
ADD COLUMN IF NOT EXISTS deal_context TEXT,
ADD COLUMN IF NOT EXISTS criteria_covered TEXT[];

-- Update existing records to have default values for new columns
UPDATE stage3_findings 
SET 
    impact_statement = COALESCE(impact_statement, ''),
    evidence_specification = COALESCE(evidence_specification, ''),
    strategic_context = COALESCE(strategic_context, ''),
    score_justification = COALESCE(score_justification, ''),
    total_score = COALESCE(total_score, 0),
    finding_level = CASE 
        WHEN COALESCE(total_score, 0) >= 9 THEN 'critical'
        WHEN COALESCE(total_score, 0) >= 7 THEN 'priority'
        ELSE 'standard'
    END
WHERE impact_statement IS NULL;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_stage3_findings_score ON stage3_findings(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_stage3_findings_level ON stage3_findings(finding_level);
CREATE INDEX IF NOT EXISTS idx_stage3_findings_client ON stage3_findings(client_id);

-- Add comments to document the structure
COMMENT ON COLUMN stage3_findings.impact_statement IS 'Lead sentence with business consequence (max 25 words)';
COMMENT ON COLUMN stage3_findings.evidence_specification IS 'Supporting detail with specific operational observation (max 35 words)';
COMMENT ON COLUMN stage3_findings.strategic_context IS 'Business significance explanation (max 2 sentences)';
COMMENT ON COLUMN stage3_findings.score_justification IS 'Breakdown of scoring criteria with point values';
COMMENT ON COLUMN stage3_findings.total_score IS 'Total weighted score (5+ = Finding, 7+ = Priority, 9+ = Critical)';
COMMENT ON COLUMN stage3_findings.finding_level IS 'critical/priority/standard based on total score';
COMMENT ON COLUMN stage3_findings.source_response_ids IS 'Array of response IDs that support this finding';

-- Update the priority_level column to use the new scoring system
UPDATE stage3_findings 
SET priority_level = CASE 
    WHEN total_score >= 9 THEN 'critical'
    WHEN total_score >= 7 THEN 'high'
    WHEN total_score >= 5 THEN 'medium'
    ELSE 'low'
END
WHERE total_score IS NOT NULL;

-- Add constraint to ensure valid scores
ALTER TABLE stage3_findings 
ADD CONSTRAINT check_total_score CHECK (total_score >= 0 AND total_score <= 12);

-- Add constraint to ensure valid finding levels
ALTER TABLE stage3_findings 
ADD CONSTRAINT check_finding_level CHECK (finding_level IN ('critical', 'priority', 'standard'));

-- Create a view for easier querying of high-quality findings
CREATE OR REPLACE VIEW high_quality_findings AS
SELECT 
    *,
    CASE 
        WHEN total_score >= 9 THEN 'Critical Finding'
        WHEN total_score >= 7 THEN 'Priority Finding'
        WHEN total_score >= 5 THEN 'Standard Finding'
        ELSE 'Below Threshold'
    END as quality_label
FROM stage3_findings 
WHERE total_score >= 5
ORDER BY total_score DESC, created_at DESC;

-- Grant permissions if needed
-- GRANT SELECT ON high_quality_findings TO your_role; 