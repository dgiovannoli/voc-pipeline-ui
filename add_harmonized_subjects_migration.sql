-- Migration: Add Harmonized Subject Columns
-- Generated automatically for LLM-based semantic harmonization integration
-- Execute these statements in your Supabase SQL editor

-- Add harmonized subject columns to stage1_data_responses
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS harmonized_subject VARCHAR(255);
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS harmonization_confidence DECIMAL(5,3);
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS harmonization_method VARCHAR(100);
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS harmonization_reasoning TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS suggested_new_category VARCHAR(255);
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS harmonized_at TIMESTAMP WITH TIME ZONE;

-- Create indexes for harmonized subjects for performance
CREATE INDEX IF NOT EXISTS idx_stage1_harmonized_subject ON stage1_data_responses(harmonized_subject);
CREATE INDEX IF NOT EXISTS idx_stage1_harmonization_confidence ON stage1_data_responses(harmonization_confidence);
CREATE INDEX IF NOT EXISTS idx_stage1_harmonized_at ON stage1_data_responses(harmonized_at);

-- Comments for documentation
COMMENT ON COLUMN stage1_data_responses.harmonized_subject IS 'LLM-mapped standardized category for cross-interview analysis';
COMMENT ON COLUMN stage1_data_responses.harmonization_confidence IS 'Confidence score (0.0-1.0) for the harmonization mapping';
COMMENT ON COLUMN stage1_data_responses.harmonization_method IS 'Method used for harmonization (llm_high_confidence, llm_medium_confidence, etc.)';
COMMENT ON COLUMN stage1_data_responses.harmonization_reasoning IS 'LLM reasoning for the harmonization decision';
COMMENT ON COLUMN stage1_data_responses.suggested_new_category IS 'New category suggested by LLM if existing categories dont fit';
COMMENT ON COLUMN stage1_data_responses.harmonized_at IS 'Timestamp when harmonization was performed'; 