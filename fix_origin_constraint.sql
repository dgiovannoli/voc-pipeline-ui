-- Fix the origin constraint to allow both 'research' and 'discovered' values
-- This will enable us to properly save discovered themes

-- First, drop the existing constraint
ALTER TABLE research_themes DROP CONSTRAINT IF EXISTS research_themes_origin_check;

-- Then, add a new constraint that allows both values
ALTER TABLE research_themes ADD CONSTRAINT research_themes_origin_check 
CHECK (origin IN ('research', 'discovered'));

-- Verify the change
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'research_themes'::regclass 
AND conname = 'research_themes_origin_check'; 