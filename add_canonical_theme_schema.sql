-- New Canonical Theme Schema
-- Implements the three-table structure recommended by the user:
-- 1. themes_raw (all uploaded themes, untouched)
-- 2. themes_canonical (merged parent themes with IDs, subjects, evidence counts)
-- 3. themes_mapping (many-to-one links with confidence + analyst decision)

-- Table 1: themes_raw - preserve all original themes for auditability
CREATE TABLE IF NOT EXISTS themes_raw (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id TEXT NOT NULL,
    original_theme_id TEXT NOT NULL, -- UUID from research_themes or interview_theme_XXX
    theme_statement TEXT NOT NULL,
    source TEXT NOT NULL, -- 'research', 'discovered', 'interview'
    subject TEXT,
    harmonized_subject TEXT,
    supporting_quotes JSONB,
    company_coverage JSONB,
    impact_score FLOAT,
    evidence_strength FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(client_id, original_theme_id)
);

-- Table 2: themes_canonical - merged parent themes for reporting
CREATE TABLE IF NOT EXISTS themes_canonical (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id TEXT NOT NULL,
    canonical_id TEXT NOT NULL, -- e.g., 'canonical_theme_001'
    subject TEXT NOT NULL,
    canonical_statement TEXT NOT NULL,
    primary_facet TEXT, -- Integration, Price, Reliability, Support, etc.
    evidence_count INTEGER DEFAULT 0,
    companies_covered INTEGER DEFAULT 0,
    confidence_score FLOAT, -- average confidence of constituent themes
    analyst_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(client_id, canonical_id)
);

-- Table 3: themes_mapping - many-to-one relationships with metadata
CREATE TABLE IF NOT EXISTS themes_mapping (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id TEXT NOT NULL,
    raw_theme_id TEXT NOT NULL, -- references themes_raw.original_theme_id
    canonical_theme_id TEXT NOT NULL, -- references themes_canonical.canonical_id
    relationship_type TEXT NOT NULL, -- 'merged_into', 'evidence_of'
    confidence_score FLOAT NOT NULL, -- cosine + noun overlap + sentiment
    analyst_decision TEXT, -- 'approved', 'denied', 'edited', 'pending'
    analyst_notes TEXT,
    merge_rationale TEXT, -- why these themes were suggested for merging
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(client_id, raw_theme_id, canonical_theme_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_themes_raw_client ON themes_raw(client_id);
CREATE INDEX IF NOT EXISTS idx_themes_raw_source ON themes_raw(source);
CREATE INDEX IF NOT EXISTS idx_themes_canonical_client ON themes_canonical(client_id);
CREATE INDEX IF NOT EXISTS idx_themes_canonical_subject ON themes_canonical(subject);
CREATE INDEX IF NOT EXISTS idx_themes_mapping_client ON themes_mapping(client_id);
CREATE INDEX IF NOT EXISTS idx_themes_mapping_raw ON themes_mapping(raw_theme_id);
CREATE INDEX IF NOT EXISTS idx_themes_mapping_canonical ON themes_mapping(canonical_theme_id);

-- Add RLS policies if needed
-- ALTER TABLE themes_raw ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE themes_canonical ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE themes_mapping ENABLE ROW LEVEL SECURITY; 