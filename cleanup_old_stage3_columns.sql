-- Clean up old columns from stage3_findings table
-- Remove columns that are no longer needed with the new Buried Wins structure

-- First, let's see what columns currently exist
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'stage3_findings' AND table_schema = 'public';

-- Drop dependent views first
DROP VIEW IF EXISTS high_quality_findings CASCADE;
DROP VIEW IF EXISTS priority_findings CASCADE;
DROP VIEW IF EXISTS critical_findings CASCADE;
DROP VIEW IF EXISTS standard_findings CASCADE;

-- Remove old columns that are no longer needed
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS finding_statement;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS enhanced_confidence;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS criteria_met;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS companies_affected;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS interviewees_affected;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS deal_impacts;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS evidence_strength;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS stakeholder_multiplier;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS impact_multiplier;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS evidence_multiplier;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS criteria_covered;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS finding_type_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS credibility_tier;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS priority_level_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS confidence_score;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_id;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS quote_ids;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS response_ids;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS company_patterns;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS cross_company_patterns;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_quotes;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_explanations;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_themes;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_criteria_scores;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_deal_impacts;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_evidence_strength;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_stakeholder_multiplier;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_impact_multiplier;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_evidence_multiplier;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_criteria_covered;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_finding_type;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_credibility_tier;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_priority_level;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_confidence_score;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_id_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS quote_ids_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS response_ids_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS company_patterns_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS cross_company_patterns_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_quotes_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_explanations_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_themes_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_criteria_scores_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_deal_impacts_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_evidence_strength_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_stakeholder_multiplier_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_impact_multiplier_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_evidence_multiplier_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_criteria_covered_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_finding_type_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_credibility_tier_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_priority_level_old;
ALTER TABLE stage3_findings DROP COLUMN IF EXISTS pattern_confidence_score_old;

-- Recreate the high_quality_findings view with the new structure
CREATE OR REPLACE VIEW high_quality_findings AS
SELECT 
    id,
    client_id,
    title,
    criterion,
    finding_type,
    impact_statement,
    evidence_specification,
    strategic_context,
    score_justification,
    total_score,
    novelty_score,
    tension_contrast_score,
    materiality_score,
    actionability_score,
    credibility_score,
    description,
    created_at
FROM stage3_findings 
WHERE total_score >= 7.0  -- High quality findings based on total score
ORDER BY total_score DESC, created_at DESC;

-- Create additional views for different quality levels
CREATE OR REPLACE VIEW priority_findings AS
SELECT * FROM stage3_findings 
WHERE total_score >= 7.0 AND total_score < 9.0
ORDER BY total_score DESC, created_at DESC;

CREATE OR REPLACE VIEW critical_findings AS
SELECT * FROM stage3_findings 
WHERE total_score >= 9.0
ORDER BY total_score DESC, created_at DESC;

CREATE OR REPLACE VIEW standard_findings AS
SELECT * FROM stage3_findings 
WHERE total_score >= 5.0 AND total_score < 7.0
ORDER BY total_score DESC, created_at DESC;

-- Verify the cleanup
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'stage3_findings' AND table_schema = 'public'
-- ORDER BY column_name;

-- Expected remaining columns should be:
-- client_id, title, criterion, finding_type, impact_statement, evidence_specification, 
-- strategic_context, score_justification, total_score, novelty_score, tension_contrast_score, 
-- materiality_score, actionability_score, credibility_score, description, created_at 