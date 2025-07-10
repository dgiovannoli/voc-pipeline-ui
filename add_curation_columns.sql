-- Add curation columns to stage4_themes table
-- Run these commands in your Supabase SQL editor

-- Add curation status column
ALTER TABLE stage4_themes 
ADD COLUMN IF NOT EXISTS curation_status VARCHAR(20) DEFAULT 'pending';

-- Add curated by column
ALTER TABLE stage4_themes 
ADD COLUMN IF NOT EXISTS curated_by VARCHAR(100);

-- Add curated at column
ALTER TABLE stage4_themes 
ADD COLUMN IF NOT EXISTS curated_at TIMESTAMP WITH TIME ZONE;

-- Add curator notes column
ALTER TABLE stage4_themes 
ADD COLUMN IF NOT EXISTS curator_notes TEXT;

-- Add curation label column for quotes (stored in JSON)
-- Note: Quotes are stored as JSON in the 'quotes' column
-- The curation labels will be stored within each quote object in the JSON array

-- Create an index on curation_status for better performance
CREATE INDEX IF NOT EXISTS idx_stage4_themes_curation_status 
ON stage4_themes(curation_status);

-- Create an index on client_id and curation_status for filtered queries
CREATE INDEX IF NOT EXISTS idx_stage4_themes_client_curation 
ON stage4_themes(client_id, curation_status);

-- Update existing themes to have 'pending' status
UPDATE stage4_themes 
SET curation_status = 'pending' 
WHERE curation_status IS NULL; 