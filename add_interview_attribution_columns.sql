-- Add interview attribution columns to stage3_findings table
ALTER TABLE stage3_findings 
ADD COLUMN interview_companies TEXT[] DEFAULT '{}',
ADD COLUMN interviewee_names TEXT[] DEFAULT '{}';

-- Update existing records to have empty arrays
UPDATE stage3_findings 
SET interview_companies = '{}', interviewee_names = '{}' 
WHERE interview_companies IS NULL OR interviewee_names IS NULL; 