-- Add missing fuzzy_grouped column to themes table
ALTER TABLE themes ADD COLUMN IF NOT EXISTS fuzzy_grouped BOOLEAN DEFAULT FALSE; 