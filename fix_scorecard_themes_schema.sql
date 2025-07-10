-- Fix scorecard_themes table schema
-- Add missing columns that the import script needs

-- Add missing columns to scorecard_themes table
ALTER TABLE scorecard_themes 
ADD COLUMN IF NOT EXISTS company_list TEXT[] DEFAULT ARRAY[]::TEXT[];

ALTER TABLE scorecard_themes 
ADD COLUMN IF NOT EXISTS stakeholder_weight_score DECIMAL(3,2) DEFAULT 0.0;

ALTER TABLE scorecard_themes 
ADD COLUMN IF NOT EXISTS quote_diversity_score DECIMAL(3,2) DEFAULT 0.0;

ALTER TABLE scorecard_themes 
ADD COLUMN IF NOT EXISTS sentiment_consistency_score DECIMAL(3,2) DEFAULT 0.0;

ALTER TABLE scorecard_themes 
ADD COLUMN IF NOT EXISTS evidence_strength DECIMAL(3,2) DEFAULT 0.0;

ALTER TABLE scorecard_themes 
ADD COLUMN IF NOT EXISTS strategic_note TEXT;

ALTER TABLE scorecard_themes 
ADD COLUMN IF NOT EXISTS competitive_positioning TEXT;

-- Add comments for documentation
COMMENT ON COLUMN scorecard_themes.company_list IS 'Array of company names represented in this theme';
COMMENT ON COLUMN scorecard_themes.stakeholder_weight_score IS 'Stakeholder weight score (0-1) based on decision-maker perspectives';
COMMENT ON COLUMN scorecard_themes.quote_diversity_score IS 'Quote diversity score (0-1) based on company representation';
COMMENT ON COLUMN scorecard_themes.sentiment_consistency_score IS 'Sentiment consistency score (0-1) across supporting quotes';
COMMENT ON COLUMN scorecard_themes.evidence_strength IS 'Evidence strength score (0-1) based on relevance scores';
COMMENT ON COLUMN scorecard_themes.strategic_note IS 'Strategic note about the importance of this theme';
COMMENT ON COLUMN scorecard_themes.competitive_positioning IS 'Competitive positioning note for this theme';

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_scorecard_themes_quality ON scorecard_themes(overall_quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_scorecard_themes_criterion ON scorecard_themes(scorecard_criterion);
CREATE INDEX IF NOT EXISTS idx_scorecard_themes_sentiment ON scorecard_themes(sentiment_direction);
CREATE INDEX IF NOT EXISTS idx_scorecard_themes_client ON scorecard_themes(client_id); 