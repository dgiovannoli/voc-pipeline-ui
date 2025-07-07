-- Add Sentiment Column
ALTER TABLE quote_analysis 
ADD COLUMN IF NOT EXISTS sentiment VARCHAR CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed'));

-- Rename Score Column to Relevance Score (PostgreSQL doesn't support IF EXISTS with RENAME)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quote_analysis' AND column_name = 'score') THEN
        ALTER TABLE quote_analysis RENAME COLUMN score TO relevance_score;
    END IF;
END $$;

-- Add Comments
COMMENT ON COLUMN quote_analysis.relevance_score IS 'Relevance/Intensity Score (0-5): 0=Not relevant, 1=Slight mention, 2=Clear mention, 3=Strong mention, 4=Very strong mention, 5=Highest possible relevance/intensity';

COMMENT ON COLUMN quote_analysis.sentiment IS 'Sentiment/Polarity: positive, negative, neutral, or mixed';

-- Create Indexes
CREATE INDEX IF NOT EXISTS idx_quote_analysis_sentiment ON quote_analysis(sentiment);

CREATE INDEX IF NOT EXISTS idx_quote_analysis_relevance_sentiment ON quote_analysis(relevance_score, sentiment);

-- Add Computed Columns
ALTER TABLE quote_analysis 
ADD COLUMN IF NOT EXISTS is_high_relevance BOOLEAN GENERATED ALWAYS AS (relevance_score >= 4) STORED;

ALTER TABLE quote_analysis 
ADD COLUMN IF NOT EXISTS is_deal_impacting BOOLEAN GENERATED ALWAYS AS (
    (relevance_score >= 4 AND sentiment = 'negative') OR 
    (relevance_score >= 4 AND sentiment = 'positive')
) STORED;

-- Create Indexes on Computed Columns
CREATE INDEX IF NOT EXISTS idx_quote_analysis_high_relevance ON quote_analysis(is_high_relevance);

CREATE INDEX IF NOT EXISTS idx_quote_analysis_deal_impacting ON quote_analysis(is_deal_impacting);

-- Update Existing Data
UPDATE quote_analysis 
SET sentiment = CASE 
    WHEN relevance_score >= 4 THEN 'negative'  -- Assume high relevance items are negative (conservative)
    WHEN relevance_score >= 3 THEN 'neutral'   -- Assume medium relevance items are neutral
    ELSE 'neutral'                              -- Assume low relevance items are neutral
END
WHERE sentiment IS NULL;

-- Add NOT NULL Constraint
ALTER TABLE quote_analysis 
ALTER COLUMN sentiment SET NOT NULL; 