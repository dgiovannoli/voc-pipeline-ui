-- Add curation fields to stage4_themes table
ALTER TABLE stage4_themes 
ADD COLUMN IF NOT EXISTS curation_status VARCHAR(20) DEFAULT 'pending' CHECK (curation_status IN ('pending', 'approved', 'denied')),
ADD COLUMN IF NOT EXISTS curated_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS curated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS curator_notes TEXT;

-- Add curation fields to quote_analysis table
ALTER TABLE quote_analysis 
ADD COLUMN IF NOT EXISTS curation_label VARCHAR(20) DEFAULT 'pending' CHECK (curation_label IN ('pending', 'approve', 'deny', 'feature')),
ADD COLUMN IF NOT EXISTS curated_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS curated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS curator_notes TEXT;

-- Create index for faster curation queries
CREATE INDEX IF NOT EXISTS idx_stage4_themes_curation_status ON stage4_themes(curation_status, client_id);
CREATE INDEX IF NOT EXISTS idx_quote_analysis_curation_label ON quote_analysis(curation_label, client_id);

-- Add comments for documentation
COMMENT ON COLUMN stage4_themes.curation_status IS 'Human curation status: pending, approved, or denied';
COMMENT ON COLUMN stage4_themes.curated_by IS 'Username of person who curated this theme';
COMMENT ON COLUMN stage4_themes.curated_at IS 'Timestamp when theme was curated';
COMMENT ON COLUMN stage4_themes.curator_notes IS 'Notes from curator about this theme';

COMMENT ON COLUMN quote_analysis.curation_label IS 'Human curation label: pending, approve, deny, or feature';
COMMENT ON COLUMN quote_analysis.curated_by IS 'Username of person who curated this quote';
COMMENT ON COLUMN quote_analysis.curated_at IS 'Timestamp when quote was curated';
COMMENT ON COLUMN quote_analysis.curator_notes IS 'Notes from curator about this quote'; 