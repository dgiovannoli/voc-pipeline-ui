-- Create findings table for Stage 3 analysis
CREATE TABLE IF NOT EXISTS findings (
    id SERIAL PRIMARY KEY,
    criterion VARCHAR(100) NOT NULL,
    finding_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    impact_score DECIMAL(3,2) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    companies_affected INTEGER NOT NULL DEFAULT 0,
    quote_count INTEGER NOT NULL DEFAULT 0,
    sample_quotes JSONB,
    themes JSONB,
    generated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_findings_criterion ON findings(criterion);
CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(finding_type);
CREATE INDEX IF NOT EXISTS idx_findings_impact ON findings(impact_score DESC);
CREATE INDEX IF NOT EXISTS idx_findings_created ON findings(created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE findings IS 'Executive findings generated from Stage 3 analysis of scored quotes';
COMMENT ON COLUMN findings.criterion IS 'The evaluation criterion this finding relates to';
COMMENT ON COLUMN findings.finding_type IS 'Type of finding: strength, improvement, positive_trend, negative_trend';
COMMENT ON COLUMN findings.title IS 'Short title for the finding';
COMMENT ON COLUMN findings.description IS 'Detailed description of the finding';
COMMENT ON COLUMN findings.impact_score IS 'Calculated impact score (0-5 scale)';
COMMENT ON COLUMN findings.confidence_score IS 'Confidence in the finding (0-1 scale)';
COMMENT ON COLUMN findings.companies_affected IS 'Number of companies this finding affects';
COMMENT ON COLUMN findings.quote_count IS 'Number of quotes supporting this finding';
COMMENT ON COLUMN findings.sample_quotes IS 'JSON array of sample quotes supporting the finding';
COMMENT ON COLUMN findings.themes IS 'JSON array of key themes identified';
COMMENT ON COLUMN findings.generated_at IS 'When the finding was generated';
COMMENT ON COLUMN findings.created_at IS 'When the record was created';

-- Enable Row Level Security (RLS)
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust as needed for your security requirements)
CREATE POLICY "Allow all operations on findings" ON findings
    FOR ALL USING (true);

-- Create themes table for Stage 4
CREATE TABLE IF NOT EXISTS themes (
    id SERIAL PRIMARY KEY,
    theme_statement TEXT NOT NULL,
    theme_category VARCHAR(50) NOT NULL,
    theme_strength VARCHAR(20) NOT NULL,
    interview_companies TEXT[] NOT NULL,
    supporting_finding_ids INTEGER[] NOT NULL,
    supporting_response_ids TEXT[] NOT NULL,
    deal_status_distribution JSONB,
    competitive_flag BOOLEAN DEFAULT FALSE,
    business_implications TEXT,
    primary_theme_quote TEXT,
    secondary_theme_quote TEXT,
    quote_attributions TEXT,
    evidence_strength VARCHAR(20),
    avg_confidence_score DECIMAL(3,2),
    company_count INTEGER,
    finding_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for themes table
CREATE INDEX IF NOT EXISTS idx_themes_category ON themes(theme_category);
CREATE INDEX IF NOT EXISTS idx_themes_strength ON themes(theme_strength);
CREATE INDEX IF NOT EXISTS idx_themes_competitive ON themes(competitive_flag);
CREATE INDEX IF NOT EXISTS idx_themes_confidence ON themes(avg_confidence_score DESC);

-- Add comments for themes table
COMMENT ON TABLE themes IS 'Stage 4 themes generated from findings analysis';
COMMENT ON COLUMN themes.theme_statement IS 'Executive-ready insight revealing business pattern';
COMMENT ON COLUMN themes.theme_category IS 'Category: Barrier, Opportunity, Strategic, Functional, Competitive';
COMMENT ON COLUMN themes.theme_strength IS 'Strength: High, Medium, Emerging';
COMMENT ON COLUMN themes.competitive_flag IS 'Whether this theme involves competitive analysis';

-- Enable RLS for themes table
ALTER TABLE themes ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for themes
CREATE POLICY "Enable read access for all users" ON themes
    FOR SELECT USING (true);

CREATE POLICY "Enable insert access for authenticated users" ON themes
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update access for authenticated users" ON themes
    FOR UPDATE USING (true);

-- Create executive_themes table for Stage 5
CREATE TABLE IF NOT EXISTS executive_themes (
    id SERIAL PRIMARY KEY,
    priority_rank INTEGER,
    theme_headline TEXT NOT NULL,
    narrative_explanation TEXT NOT NULL,
    primary_executive_quote TEXT,
    secondary_executive_quote TEXT,
    quote_attribution TEXT,
    theme_category VARCHAR(50),
    supporting_evidence_summary TEXT,
    business_impact_level VARCHAR(20),
    competitive_context TEXT,
    strategic_recommendations TEXT,
    original_theme_id INTEGER REFERENCES themes(id),
    priority_score DECIMAL(4,2),
    executive_readiness VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for executive_themes table
CREATE INDEX IF NOT EXISTS idx_executive_themes_priority ON executive_themes(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_executive_themes_category ON executive_themes(theme_category);
CREATE INDEX IF NOT EXISTS idx_executive_themes_impact ON executive_themes(business_impact_level);
CREATE INDEX IF NOT EXISTS idx_executive_themes_created ON executive_themes(created_at DESC);

-- Add comments for executive_themes table
COMMENT ON TABLE executive_themes IS 'Stage 5 executive synthesis themes ready for C-suite presentation';
COMMENT ON COLUMN executive_themes.theme_headline IS 'Executive-ready headline following punch-then-explain principle';
COMMENT ON COLUMN executive_themes.narrative_explanation IS '2-3 sentence business narrative connecting pattern to strategic value';
COMMENT ON COLUMN executive_themes.business_impact_level IS 'Impact level: High, Medium, Emerging';
COMMENT ON COLUMN executive_themes.executive_readiness IS 'Readiness: Presentation, Report, Follow-up';

-- Enable RLS for executive_themes table
ALTER TABLE executive_themes ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for executive_themes
CREATE POLICY "Enable read access for all users" ON executive_themes
    FOR SELECT USING (true);

CREATE POLICY "Enable insert access for authenticated users" ON executive_themes
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update access for authenticated users" ON executive_themes
    FOR UPDATE USING (true);

-- Create criteria_scorecard table for Stage 5
CREATE TABLE IF NOT EXISTS criteria_scorecard (
    id SERIAL PRIMARY KEY,
    criterion VARCHAR(100) NOT NULL,
    performance_rating VARCHAR(20) NOT NULL,
    avg_score DECIMAL(3,2) NOT NULL,
    total_mentions INTEGER NOT NULL,
    companies_affected INTEGER NOT NULL,
    critical_mentions INTEGER NOT NULL,
    executive_priority VARCHAR(20) NOT NULL,
    action_urgency VARCHAR(20) NOT NULL,
    trend_direction VARCHAR(20) NOT NULL,
    key_insights TEXT,
    sample_quotes JSONB,
    deal_impact_analysis JSONB,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for criteria_scorecard table
CREATE INDEX IF NOT EXISTS idx_scorecard_rating ON criteria_scorecard(performance_rating);
CREATE INDEX IF NOT EXISTS idx_scorecard_priority ON criteria_scorecard(executive_priority);
CREATE INDEX IF NOT EXISTS idx_scorecard_generated ON criteria_scorecard(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_scorecard_criterion ON criteria_scorecard(criterion);

-- Add comments for criteria_scorecard table
COMMENT ON TABLE criteria_scorecard IS 'Stage 5 criteria performance scorecard for executive review';
COMMENT ON COLUMN criteria_scorecard.performance_rating IS 'Rating: EXCEPTIONAL, STRONG, GOOD, NEEDS ATTENTION, CRITICAL ISSUE';
COMMENT ON COLUMN criteria_scorecard.executive_priority IS 'Priority: IMMEDIATE ACTION, HIGH PRIORITY, MEDIUM PRIORITY, MONITOR';
COMMENT ON COLUMN criteria_scorecard.action_urgency IS 'Urgency: HIGH, MEDIUM, LOW';

-- Create enhanced_findings table for Buried Wins v4.0 framework
CREATE TABLE IF NOT EXISTS enhanced_findings (
    id SERIAL PRIMARY KEY,
    criterion VARCHAR(100) NOT NULL,
    finding_type VARCHAR(50) NOT NULL,
    priority_level VARCHAR(20) DEFAULT 'standard',
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    enhanced_confidence DECIMAL(4,2) NOT NULL,
    criteria_scores JSONB,
    criteria_met INTEGER DEFAULT 0,
    impact_score DECIMAL(4,2),
    companies_affected INTEGER DEFAULT 0,
    quote_count INTEGER DEFAULT 0,
    selected_quotes JSONB,
    themes JSONB,
    deal_impacts JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_enhanced_findings_criterion ON enhanced_findings(criterion);
CREATE INDEX IF NOT EXISTS idx_enhanced_findings_priority ON enhanced_findings(priority_level);
CREATE INDEX IF NOT EXISTS idx_enhanced_findings_confidence ON enhanced_findings(enhanced_confidence DESC);
CREATE INDEX IF NOT EXISTS idx_enhanced_findings_type ON enhanced_findings(finding_type);

-- Add comments for documentation
COMMENT ON TABLE enhanced_findings IS 'Enhanced findings with Buried Wins v4.0 framework and automated confidence scoring';
COMMENT ON COLUMN enhanced_findings.enhanced_confidence IS 'Confidence score (0-10) based on Buried Wins v4.0 criteria';
COMMENT ON COLUMN enhanced_findings.criteria_scores IS 'JSON object with scores for each of the 8 evaluation criteria';
COMMENT ON COLUMN enhanced_findings.criteria_met IS 'Number of evaluation criteria met (2-8)';
COMMENT ON COLUMN enhanced_findings.priority_level IS 'Priority classification: priority (≥4.0), standard (≥3.0), low (<3.0)';
COMMENT ON COLUMN enhanced_findings.selected_quotes IS 'JSON array of optimally selected quotes with attribution';
COMMENT ON COLUMN enhanced_findings.themes IS 'JSON array of extracted themes from the finding';
COMMENT ON COLUMN enhanced_findings.deal_impacts IS 'JSON object with deal impact analysis';

-- Create legacy findings table for backward compatibility
CREATE TABLE IF NOT EXISTS legacy_findings (
    id SERIAL PRIMARY KEY,
    criterion VARCHAR(100) NOT NULL,
    finding_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    impact_score DECIMAL(4,2),
    confidence_score DECIMAL(4,2),
    companies_affected INTEGER DEFAULT 0,
    quote_count INTEGER DEFAULT 0,
    sample_quotes JSONB,
    themes JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for legacy table
CREATE INDEX IF NOT EXISTS idx_legacy_findings_criterion ON legacy_findings(criterion);
CREATE INDEX IF NOT EXISTS idx_legacy_findings_type ON legacy_findings(finding_type); 