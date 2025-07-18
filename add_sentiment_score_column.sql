-- Add sentiment_score column to stage2_response_labeling table
-- This supports the new -5 to +5 sentiment scoring system

ALTER TABLE stage2_response_labeling 
ADD COLUMN IF NOT EXISTS sentiment_score DECIMAL(3,1) CHECK (sentiment_score >= -5 AND sentiment_score <= 5);

-- Add comment for documentation
COMMENT ON COLUMN stage2_response_labeling.sentiment_score IS 'Sentiment score from -5 (extremely negative) to +5 (extremely positive)';

-- Add index for sentiment_score for efficient querying
CREATE INDEX IF NOT EXISTS idx_stage2_sentiment_score ON stage2_response_labeling(sentiment_score);

-- Update existing records to have default sentiment_score of 0
UPDATE stage2_response_labeling 
SET sentiment_score = CASE 
    WHEN sentiment = 'positive' THEN 3.0
    WHEN sentiment = 'negative' THEN -3.0
    WHEN sentiment = 'mixed' THEN 0.0
    ELSE 0.0  -- neutral
END
WHERE sentiment_score IS NULL; 