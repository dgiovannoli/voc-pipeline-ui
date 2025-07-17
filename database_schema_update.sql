-- Database Schema Update for Interview ID Extraction System
-- Generated automatically

-- Add interview_id column
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_id TEXT;

-- Add metadata columns
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS client_name TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS industry TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS segment TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS contact_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_list_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS project_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS scheduled_date TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_method TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_status TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS moderator_notes TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS flag_details TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS flag_type TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS payment_complete TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS transcript_link TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS audio/video_link TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_full_name TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_company_name TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS job_title_(from_contact_id) TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_email TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_mobile_phone_number TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_question_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_response_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS discussion_guide_link TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_website TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS client_website TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS moderator_responses TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS final_incentive_amount TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS completion_date TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS auto_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS deal_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS company_match_key TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS base_incentive_amount TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS escalated_incentive_amount TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS incentive_change_date TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS custom_incentive TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS custom_incentive_amount TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_guide_context TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_guides_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS linkedin_profile_(from_contact_id) TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS recruitment_records TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS moderators TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS moderator_score TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_stage1_interview_id ON stage1_data_responses(interview_id);
CREATE INDEX IF NOT EXISTS idx_stage1_client_name ON stage1_data_responses(client_name);
CREATE INDEX IF NOT EXISTS idx_stage1_deal_status ON stage1_data_responses(deal_status);
CREATE INDEX IF NOT EXISTS idx_stage1_industry ON stage1_data_responses(industry);
CREATE INDEX IF NOT EXISTS idx_stage1_segment ON stage1_data_responses(segment);

-- Add comments
COMMENT ON COLUMN stage1_data_responses.interview_id IS 'Interview ID from metadata (format: IVL-XXXXX)';