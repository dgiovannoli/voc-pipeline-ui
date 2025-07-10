-- Add interview_id column to stage2_response_labeling table
ALTER TABLE stage2_response_labeling 
ADD COLUMN interview_id INTEGER;

-- Add index for better query performance
CREATE INDEX idx_stage2_response_labeling_interview_id ON stage2_response_labeling(interview_id);

-- Update existing records to have NULL interview_id (will be populated later)
UPDATE stage2_response_labeling 
SET interview_id = NULL 
WHERE interview_id IS NULL;

-- Add comment to document the column purpose
COMMENT ON COLUMN stage2_response_labeling.interview_id IS 'Foreign key to interviewee metadata mapping table'; 