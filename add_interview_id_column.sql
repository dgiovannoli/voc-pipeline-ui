-- Add interview_id column to quote_analysis table
ALTER TABLE quote_analysis 
ADD COLUMN interview_id INTEGER;

-- Add index for better query performance
CREATE INDEX idx_quote_analysis_interview_id ON quote_analysis(interview_id);

-- Update existing records to have NULL interview_id (will be populated later)
UPDATE quote_analysis 
SET interview_id = NULL 
WHERE interview_id IS NULL;

-- Add comment to document the column purpose
COMMENT ON COLUMN quote_analysis.interview_id IS 'Foreign key to interviewee metadata mapping table'; 