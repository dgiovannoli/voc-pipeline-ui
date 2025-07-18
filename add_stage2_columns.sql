-- Add new columns to stage2_response_labeling table for improved analysis
-- This supports 1 record per quote with primary/secondary/tertiary criteria

ALTER TABLE stage2_response_labeling 
ADD COLUMN IF NOT EXISTS secondary_criterion VARCHAR(100),
ADD COLUMN IF NOT EXISTS tertiary_criterion VARCHAR(100),
ADD COLUMN IF NOT EXISTS all_relevance_scores JSONB;

-- Add comments for documentation
COMMENT ON COLUMN stage2_response_labeling.secondary_criterion IS 'Second most relevant criterion for this quote (if applicable)';
COMMENT ON COLUMN stage2_response_labeling.tertiary_criterion IS 'Third most relevant criterion for this quote (if applicable)';
COMMENT ON COLUMN stage2_response_labeling.all_relevance_scores IS 'JSON object containing relevance scores for all identified criteria';

-- Add indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_stage2_secondary_criterion ON stage2_response_labeling(secondary_criterion);
CREATE INDEX IF NOT EXISTS idx_stage2_tertiary_criterion ON stage2_response_labeling(tertiary_criterion);
CREATE INDEX IF NOT EXISTS idx_stage2_all_relevance_scores_gin ON stage2_response_labeling USING GIN (all_relevance_scores); 