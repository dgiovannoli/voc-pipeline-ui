-- Add quality control columns to themes table
ALTER TABLE themes 
ADD COLUMN quality_decision TEXT DEFAULT 'Pending' CHECK (quality_decision IN ('Pending', 'Approved', 'Rejected', 'Featured')),
ADD COLUMN quality_notes TEXT,
ADD COLUMN reviewed_at TIMESTAMP,
ADD COLUMN reviewed_by TEXT;

-- Create index for faster filtering
CREATE INDEX idx_themes_quality_decision ON themes(quality_decision);

-- Add comment for documentation
COMMENT ON COLUMN themes.quality_decision IS 'Human review decision: Pending, Approved, Rejected, or Featured';
COMMENT ON COLUMN themes.quality_notes IS 'Reviewer notes explaining the decision';
COMMENT ON COLUMN themes.reviewed_at IS 'Timestamp when theme was reviewed';
COMMENT ON COLUMN themes.reviewed_by IS 'Username of the reviewer'; 