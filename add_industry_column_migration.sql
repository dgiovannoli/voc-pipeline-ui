-- Migration to add industry column to stage1_data_responses table
-- Run this script to update existing database schema

-- Add industry column to stage1_data_responses table
ALTER TABLE stage1_data_responses 
ADD COLUMN IF NOT EXISTS industry VARCHAR(255);

-- Add index for the new industry column
CREATE INDEX IF NOT EXISTS idx_stage1_industry ON stage1_data_responses(industry);

-- Update existing records to have a default industry value if needed
-- UPDATE stage1_data_responses SET industry = 'Unknown' WHERE industry IS NULL;

-- Verify the column was added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'stage1_data_responses' 
AND column_name = 'industry'; 