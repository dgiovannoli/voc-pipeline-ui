-- Add research question alignment columns to stage1_data_responses table
-- Run this SQL in your Supabase database

ALTER TABLE stage1_data_responses 
ADD COLUMN IF NOT EXISTS research_question_alignment TEXT,
ADD COLUMN IF NOT EXISTS total_questions_addressed INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS coverage_summary TEXT,
ADD COLUMN IF NOT EXISTS stage2_analysis_timestamp TIMESTAMP WITH TIME ZONE;

-- Verify the columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'stage1_data_responses' 
AND column_name IN ('research_question_alignment', 'total_questions_addressed', 'coverage_summary', 'stage2_analysis_timestamp')
ORDER BY column_name; 