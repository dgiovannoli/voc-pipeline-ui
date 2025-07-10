-- Update stage2_response_labeling table to separate relevance/intensity from sentiment
-- This implements the new scoring system recommended by the user

-- Add new sentiment column
ALTER TABLE stage2_response_labeling ADD COLUMN sentiment VARCHAR CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed'));

-- Rename existing score column to relevance_score for clarity
ALTER TABLE stage2_response_labeling RENAME COLUMN score TO relevance_score;

-- Add comment to clarify the new scoring system
COMMENT ON COLUMN stage2_response_labeling.relevance_score IS 'Relevance/Intensity Score (0-5): 0=Not relevant, 1=Slight mention, 2=Clear mention, 3=Strong mention, 4=Very strong mention, 5=Highest possible relevance/intensity';
COMMENT ON COLUMN stage2_response_labeling.sentiment IS 'Sentiment/Polarity: positive, negative, neutral, or mixed';

-- Update the deal_weighted_score column comment to reflect it's now based on relevance_score
COMMENT ON COLUMN stage2_response_labeling.deal_weighted_score IS 'Deal-weighted relevance score (based on relevance_score with deal status adjustments)';

-- Create index on sentiment for efficient filtering
CREATE INDEX idx_stage2_response_labeling_sentiment ON stage2_response_labeling(sentiment);

-- Create composite index for relevance + sentiment queries
CREATE INDEX idx_stage2_response_labeling_relevance_sentiment ON stage2_response_labeling(relevance_score, sentiment);

-- Add a computed column for easy filtering of high-relevance items
ALTER TABLE stage2_response_labeling ADD COLUMN is_high_relevance BOOLEAN GENERATED ALWAYS AS (relevance_score >= 4) STORED;

-- Add a computed column for easy filtering of deal-impacting items
ALTER TABLE stage2_response_labeling ADD COLUMN is_deal_impacting BOOLEAN GENERATED ALWAYS AS (
    (relevance_score >= 4 AND sentiment = 'negative') OR 
    (relevance_score >= 4 AND sentiment = 'positive')
) STORED;

-- Create index on computed columns
CREATE INDEX idx_stage2_response_labeling_high_relevance ON stage2_response_labeling(is_high_relevance);
CREATE INDEX idx_stage2_response_labeling_deal_impacting ON stage2_response_labeling(is_deal_impacting);

-- Update existing data to have default sentiment values
-- This is a temporary measure until we reprocess the data
UPDATE stage2_response_labeling 
SET sentiment = CASE 
    WHEN relevance_score >= 4 THEN 'negative'  -- Assume high relevance items are negative (conservative)
    WHEN relevance_score >= 3 THEN 'neutral'   -- Assume medium relevance items are neutral
    ELSE 'neutral'                              -- Assume low relevance items are neutral
END
WHERE sentiment IS NULL;

-- Add NOT NULL constraint after setting default values
ALTER TABLE stage2_response_labeling ALTER COLUMN sentiment SET NOT NULL; 