-- Add embedding column to quote_analysis table for vector similarity
-- This enables semantic search and deduplication for quote analysis data

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column for OpenAI (1536-dim) embeddings
ALTER TABLE quote_analysis ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create index for vector similarity searches
CREATE INDEX IF NOT EXISTS idx_quote_analysis_embedding ON quote_analysis USING ivfflat (embedding vector_cosine_ops);

-- Add comment for documentation
COMMENT ON COLUMN quote_analysis.embedding IS 'OpenAI text-embedding-ada-002 embedding for relevance_explanation field (1536 dimensions)';

-- Verify the column was added
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'quote_analysis' 
AND column_name = 'embedding'; 