-- Add Sentiment Column
ALTER TABLE stage2_response_labeling 
ADD COLUMN IF NOT EXISTS sentiment VARCHAR CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed'));

-- Rename Score Column to Relevance Score (PostgreSQL doesn't support IF EXISTS with RENAME)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stage2_response_labeling' AND column_name = 'score') THEN
        ALTER TABLE stage2_response_labeling RENAME COLUMN score TO relevance_score;
    END IF;
END $$;

-- Add Comments
COMMENT ON COLUMN stage2_response_labeling.relevance_score IS 'Relevance/Intensity Score (0-5): 0=Not relevant, 1=Slight mention, 2=Clear mention, 3=Strong mention, 4=Very strong mention, 5=Highest possible relevance/intensity';

COMMENT ON COLUMN stage2_response_labeling.sentiment IS 'Sentiment/Polarity: positive, negative, neutral, or mixed';

-- Create Indexes
CREATE INDEX IF NOT EXISTS idx_stage2_response_labeling_sentiment ON stage2_response_labeling(sentiment);

CREATE INDEX IF NOT EXISTS idx_stage2_response_labeling_relevance_sentiment ON stage2_response_labeling(relevance_score, sentiment);

-- Add Computed Columns
ALTER TABLE stage2_response_labeling 
ADD COLUMN IF NOT EXISTS is_high_relevance BOOLEAN GENERATED ALWAYS AS (relevance_score >= 4) STORED;

ALTER TABLE stage2_response_labeling 
ADD COLUMN IF NOT EXISTS is_deal_impacting BOOLEAN GENERATED ALWAYS AS (
    (relevance_score >= 4 AND sentiment = 'negative') OR 
    (relevance_score >= 4 AND sentiment = 'positive')
) STORED;

-- Create Indexes on Computed Columns
CREATE INDEX IF NOT EXISTS idx_stage2_response_labeling_high_relevance ON stage2_response_labeling(is_high_relevance);

CREATE INDEX IF NOT EXISTS idx_stage2_response_labeling_deal_impacting ON stage2_response_labeling(is_deal_impacting);

-- Update Existing Data
UPDATE stage2_response_labeling 
SET sentiment = CASE 
    WHEN relevance_score >= 4 THEN 'negative'  -- Assume high relevance items are negative (conservative)
    WHEN relevance_score >= 3 THEN 'neutral'   -- Assume medium relevance items are neutral
    ELSE 'neutral'                              -- Assume low relevance items are neutral
END
WHERE sentiment IS NULL;

-- Add NOT NULL Constraint
ALTER TABLE stage2_response_labeling 
ALTER COLUMN sentiment SET NOT NULL; 