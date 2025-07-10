-- Check if interview_id column exists and its current state
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'stage2_response_labeling' 
AND column_name = 'interview_id';

-- Check if index exists
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'stage2_response_labeling' 
AND indexname LIKE '%interview_id%';

-- Check current data in interview_id column (sample)
SELECT 
    interview_id,
    COUNT(*) as count
FROM stage2_response_labeling 
GROUP BY interview_id 
ORDER BY interview_id 
LIMIT 10; 