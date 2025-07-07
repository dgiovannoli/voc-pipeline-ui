# Manual Database Schema Update Guide

Since `psql` is not available, you'll need to update the database schema manually through the Supabase dashboard.

## Step 1: Access Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor** in the left sidebar

## Step 2: Execute Schema Updates

Copy and paste the following SQL commands one by one into the SQL Editor:

### 1. Add Sentiment Column
```sql
ALTER TABLE quote_analysis 
ADD COLUMN IF NOT EXISTS sentiment VARCHAR CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed'));
```

### 2. Rename Score Column to Relevance Score
```sql
ALTER TABLE quote_analysis 
RENAME COLUMN IF EXISTS score TO relevance_score;
```

### 3. Add Comments
```sql
COMMENT ON COLUMN quote_analysis.relevance_score IS 'Relevance/Intensity Score (0-5): 0=Not relevant, 1=Slight mention, 2=Clear mention, 3=Strong mention, 4=Very strong mention, 5=Highest possible relevance/intensity';
```

```sql
COMMENT ON COLUMN quote_analysis.sentiment IS 'Sentiment/Polarity: positive, negative, neutral, or mixed';
```

### 4. Create Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_quote_analysis_sentiment ON quote_analysis(sentiment);
```

```sql
CREATE INDEX IF NOT EXISTS idx_quote_analysis_relevance_sentiment ON quote_analysis(relevance_score, sentiment);
```

### 5. Add Computed Columns
```sql
ALTER TABLE quote_analysis 
ADD COLUMN IF NOT EXISTS is_high_relevance BOOLEAN GENERATED ALWAYS AS (relevance_score >= 4) STORED;
```

```sql
ALTER TABLE quote_analysis 
ADD COLUMN IF NOT EXISTS is_deal_impacting BOOLEAN GENERATED ALWAYS AS (
    (relevance_score >= 4 AND sentiment = 'negative') OR 
    (relevance_score >= 4 AND sentiment = 'positive')
) STORED;
```

### 6. Create Indexes on Computed Columns
```sql
CREATE INDEX IF NOT EXISTS idx_quote_analysis_high_relevance ON quote_analysis(is_high_relevance);
```

```sql
CREATE INDEX IF NOT EXISTS idx_quote_analysis_deal_impacting ON quote_analysis(is_deal_impacting);
```

### 7. Update Existing Data
```sql
UPDATE quote_analysis 
SET sentiment = CASE 
    WHEN relevance_score >= 4 THEN 'negative'  -- Assume high relevance items are negative (conservative)
    WHEN relevance_score >= 3 THEN 'neutral'   -- Assume medium relevance items are neutral
    ELSE 'neutral'                              -- Assume low relevance items are neutral
END
WHERE sentiment IS NULL;
```

### 8. Add NOT NULL Constraint
```sql
ALTER TABLE quote_analysis 
ALTER COLUMN sentiment SET NOT NULL;
```

## Step 3: Verify Changes

After running all the SQL commands, you can verify the changes by running:

```sql
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'quote_analysis' 
ORDER BY ordinal_position;
```

This should show the new columns:
- `relevance_score` (renamed from `score`)
- `sentiment`
- `is_high_relevance`
- `is_deal_impacting`

## Step 4: Test the Implementation

After updating the schema, run:

```bash
python test_new_scoring_system.py
```

This should now show:
- ✅ relevance_score column exists
- ✅ sentiment column exists
- ✅ All tests passing

## Alternative: Use Supabase CLI

If you have the Supabase CLI installed, you can also run:

```bash
# Install Supabase CLI if you don't have it
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref YOUR_PROJECT_REF

# Run the schema update
supabase db push
```

## Troubleshooting

If you encounter any errors:

1. **Column already exists**: Skip that command and continue with the next one
2. **Permission errors**: Make sure you're using the correct database role
3. **Constraint violations**: Check if there's existing data that conflicts with the new constraints

## Next Steps After Schema Update

1. **Reprocess Stage 2 data** to get proper relevance/sentiment scores:
   ```bash
   python enhanced_stage2_analyzer.py --force_reprocess --client_id Rev
   ```

2. **Regenerate Stage 4 themes** with new scoring data:
   ```bash
   python stage4_theme_analyzer.py --client_id Rev
   ```

3. **Test the UI** to see the improved scoring display

## Summary

The manual schema update will:
- ✅ Add sentiment column with constraints
- ✅ Rename score to relevance_score
- ✅ Add computed columns for filtering
- ✅ Create indexes for performance
- ✅ Update existing data with default sentiment values

Once completed, the new scoring system will be fully functional! 