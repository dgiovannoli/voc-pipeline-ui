-- Add fields to interview_metadata table for comprehensive metadata storage
-- This migration adds fields to support the full metadata CSV structure

-- Add new columns to interview_metadata table
ALTER TABLE interview_metadata 
ADD COLUMN IF NOT EXISTS contact_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS interview_list_id_deals VARCHAR(255),
ADD COLUMN IF NOT EXISTS interview_list_id_direct VARCHAR(255),
ADD COLUMN IF NOT EXISTS project_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS scheduled_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(255),
ADD COLUMN IF NOT EXISTS moderator_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS interview_method VARCHAR(100),
ADD COLUMN IF NOT EXISTS conversion_source VARCHAR(255),
ADD COLUMN IF NOT EXISTS interview_status VARCHAR(100),
ADD COLUMN IF NOT EXISTS moderator_notes TEXT,
ADD COLUMN IF NOT EXISTS flag_details TEXT,
ADD COLUMN IF NOT EXISTS flag_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS payment_complete BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS transcript_link TEXT,
ADD COLUMN IF NOT EXISTS audio_video_link TEXT,
ADD COLUMN IF NOT EXISTS interview_contact_website TEXT,
ADD COLUMN IF NOT EXISTS job_title VARCHAR(255),
ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS contact_mobile VARCHAR(255),
ADD COLUMN IF NOT EXISTS interview_question_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS interview_response_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS discussion_guide_link TEXT,
ADD COLUMN IF NOT EXISTS client_website TEXT,
ADD COLUMN IF NOT EXISTS moderator_responses TEXT,
ADD COLUMN IF NOT EXISTS final_incentive_amount DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS completion_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS auto_id INTEGER,
ADD COLUMN IF NOT EXISTS deal_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS company_match_key VARCHAR(255),
ADD COLUMN IF NOT EXISTS base_incentive_amount DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS escalated_incentive_amount DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS incentive_change_date DATE,
ADD COLUMN IF NOT EXISTS custom_incentive BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS custom_incentive_amount DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS interview_guide_context TEXT,
ADD COLUMN IF NOT EXISTS interview_guides_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS linkedin_profile TEXT,
ADD COLUMN IF NOT EXISTS recruitment_records TEXT,
ADD COLUMN IF NOT EXISTS moderators TEXT,
ADD COLUMN IF NOT EXISTS moderator_score DECIMAL(3,1),
ADD COLUMN IF NOT EXISTS segment VARCHAR(255),
ADD COLUMN IF NOT EXISTS raw_transcript TEXT,
ADD COLUMN IF NOT EXISTS raw_transcript_file TEXT,
ADD COLUMN IF NOT EXISTS last_modified_time TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS interview_guides TEXT,
ADD COLUMN IF NOT EXISTS metadata_uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS metadata_source VARCHAR(255) DEFAULT 'csv_upload';

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_interview_metadata_project_id ON interview_metadata(project_id);
CREATE INDEX IF NOT EXISTS idx_interview_metadata_deal_id ON interview_metadata(deal_id);
CREATE INDEX IF NOT EXISTS idx_interview_metadata_contact_id ON interview_metadata(contact_id);
CREATE INDEX IF NOT EXISTS idx_interview_metadata_scheduled_date ON interview_metadata(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_interview_metadata_completion_date ON interview_metadata(completion_date);

-- Add comments to document the new fields
COMMENT ON COLUMN interview_metadata.contact_id IS 'Unique identifier for the contact person';
COMMENT ON COLUMN interview_metadata.interview_list_id_deals IS 'Interview list ID for deals lookup';
COMMENT ON COLUMN interview_metadata.interview_list_id_direct IS 'Interview list ID for direct link';
COMMENT ON COLUMN interview_metadata.project_id IS 'Project identifier (e.g., Endicia_PRJ-00025)';
COMMENT ON COLUMN interview_metadata.scheduled_date IS 'When the interview was scheduled';
COMMENT ON COLUMN interview_metadata.contact_phone IS 'Contact phone number';
COMMENT ON COLUMN interview_metadata.moderator_email IS 'Email of the interview moderator';
COMMENT ON COLUMN interview_metadata.interview_method IS 'Method used for interview (e.g., zoom, phone)';
COMMENT ON COLUMN interview_metadata.conversion_source IS 'Source of the interview conversion';
COMMENT ON COLUMN interview_metadata.interview_status IS 'Current status of the interview';
COMMENT ON COLUMN interview_metadata.moderator_notes IS 'Notes from the moderator';
COMMENT ON COLUMN interview_metadata.flag_details IS 'Details about any flags';
COMMENT ON COLUMN interview_metadata.flag_type IS 'Type of flag applied';
COMMENT ON COLUMN interview_metadata.payment_complete IS 'Whether payment is complete';
COMMENT ON COLUMN interview_metadata.transcript_link IS 'Link to the transcript';
COMMENT ON COLUMN interview_metadata.audio_video_link IS 'Link to audio/video recording';
COMMENT ON COLUMN interview_metadata.interview_contact_website IS 'Website of the contact/company';
COMMENT ON COLUMN interview_metadata.job_title IS 'Job title of the contact';
COMMENT ON COLUMN interview_metadata.contact_email IS 'Email of the contact';
COMMENT ON COLUMN interview_metadata.contact_mobile IS 'Mobile phone of the contact';
COMMENT ON COLUMN interview_metadata.interview_question_id IS 'ID of the interview question';
COMMENT ON COLUMN interview_metadata.interview_response_id IS 'ID of the interview response';
COMMENT ON COLUMN interview_metadata.discussion_guide_link IS 'Link to discussion guide';
COMMENT ON COLUMN interview_metadata.client_website IS 'Website of the client';
COMMENT ON COLUMN interview_metadata.moderator_responses IS 'Responses from the moderator';
COMMENT ON COLUMN interview_metadata.final_incentive_amount IS 'Final incentive amount paid';
COMMENT ON COLUMN interview_metadata.completion_date IS 'When the interview was completed';
COMMENT ON COLUMN interview_metadata.auto_id IS 'Auto-generated ID';
COMMENT ON COLUMN interview_metadata.deal_id IS 'Associated deal ID';
COMMENT ON COLUMN interview_metadata.company_match_key IS 'Key for matching companies';
COMMENT ON COLUMN interview_metadata.base_incentive_amount IS 'Base incentive amount';
COMMENT ON COLUMN interview_metadata.escalated_incentive_amount IS 'Escalated incentive amount';
COMMENT ON COLUMN interview_metadata.incentive_change_date IS 'Date incentive was changed';
COMMENT ON COLUMN interview_metadata.custom_incentive IS 'Whether custom incentive was used';
COMMENT ON COLUMN interview_metadata.custom_incentive_amount IS 'Amount of custom incentive';
COMMENT ON COLUMN interview_metadata.interview_guide_context IS 'Context for interview guide';
COMMENT ON COLUMN interview_metadata.interview_guides_id IS 'ID of interview guides';
COMMENT ON COLUMN interview_metadata.linkedin_profile IS 'LinkedIn profile URL';
COMMENT ON COLUMN interview_metadata.recruitment_records IS 'Recruitment records';
COMMENT ON COLUMN interview_metadata.moderators IS 'List of moderators';
COMMENT ON COLUMN interview_metadata.moderator_score IS 'Score given to moderator';
COMMENT ON COLUMN interview_metadata.segment IS 'Segment classification';
COMMENT ON COLUMN interview_metadata.raw_transcript IS 'Raw transcript text';
COMMENT ON COLUMN interview_metadata.raw_transcript_file IS 'Raw transcript file';
COMMENT ON COLUMN interview_metadata.last_modified_time IS 'Last time record was modified';
COMMENT ON COLUMN interview_metadata.interview_guides IS 'Interview guides used';
COMMENT ON COLUMN interview_metadata.metadata_uploaded_at IS 'When metadata was uploaded';
COMMENT ON COLUMN interview_metadata.metadata_source IS 'Source of the metadata';

-- Update existing records to set default values
UPDATE interview_metadata 
SET 
    metadata_uploaded_at = COALESCE(metadata_uploaded_at, NOW()),
    metadata_source = COALESCE(metadata_source, 'legacy')
WHERE metadata_uploaded_at IS NULL OR metadata_source IS NULL;

-- Create a view for easy access to key metadata
CREATE OR REPLACE VIEW interview_metadata_summary AS
SELECT 
    id,
    client_id,
    interview_id,
    interviewee_name,
    company,
    industry,
    project_id,
    scheduled_date,
    completion_date,
    interview_status,
    deal_status,
    contact_email,
    contact_phone,
    job_title,
    interview_method,
    transcript_link,
    audio_video_link,
    final_incentive_amount,
    moderator_score,
    metadata_uploaded_at
FROM interview_metadata;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT ON interview_metadata_summary TO authenticated;
-- GRANT ALL ON interview_metadata TO authenticated; 