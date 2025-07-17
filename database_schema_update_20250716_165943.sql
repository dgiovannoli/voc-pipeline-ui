-- Database Schema Update for Interview ID Extraction
-- Generated on: 2025-07-16T16:59:43.403596
-- Execute these statements in your Supabase SQL editor

ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_id TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS client_name TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS deal_status TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS industry TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS segment TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS contact_id INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_list_id INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS project_id INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS scheduled_date DATE;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_method TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_status TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS moderator_notes TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS flag_details TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS flag_type TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS payment_complete TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS transcript_link TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS audio/video_link INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_full_name TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_company_name TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS job_title_(from_contact_id) INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_email TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_mobile_phone_number INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_question_id INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_response_id INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS discussion_guide_link INTEGER;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS interview_contact_website TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS client_website TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS moderators TEXT;
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS moderator_score INTEGER;
CREATE INDEX IF NOT EXISTS idx_stage1_interview_id ON stage1_data_responses(interview_id);
CREATE INDEX IF NOT EXISTS idx_stage1_client_name ON stage1_data_responses(client_name);
CREATE INDEX IF NOT EXISTS idx_stage1_deal_status ON stage1_data_responses(deal_status);
CREATE INDEX IF NOT EXISTS idx_stage1_company ON stage1_data_responses(company);
COMMENT ON COLUMN stage1_data_responses.interview_id IS 'Interview ID from metadata (format: IVL-XXXXX)';
