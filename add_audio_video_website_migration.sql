-- Migration to add audio_video_link and contact_website columns to stage1_data_responses table
-- Run this script to update existing database schema

-- Add audio_video_link column to stage1_data_responses table
ALTER TABLE stage1_data_responses 
ADD COLUMN IF NOT EXISTS audio_video_link TEXT;

-- Add contact_website column to stage1_data_responses table
ALTER TABLE stage1_data_responses 
ADD COLUMN IF NOT EXISTS contact_website VARCHAR(500);

-- Add indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_stage1_audio_video_link ON stage1_data_responses(audio_video_link);
CREATE INDEX IF NOT EXISTS idx_stage1_contact_website ON stage1_data_responses(contact_website);

-- Verify the columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'stage1_data_responses' 
AND column_name IN ('audio_video_link', 'contact_website')
ORDER BY column_name; 