-- Stage 4 Themes Schema - Complete Update
-- This schema supports the comprehensive B2B SaaS Win/Loss Theme Development Protocol

-- Drop the dependent view first
DROP VIEW IF EXISTS stage4_themes_summary;

-- Drop the existing table
DROP TABLE IF EXISTS stage4_themes;

-- Create the new stage4_themes table
CREATE TABLE stage4_themes (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    theme_id VARCHAR(255) NOT NULL,
    theme_type VARCHAR(50) DEFAULT 'theme', -- 'theme' or 'strategic_alert'
    competitive_flag BOOLEAN DEFAULT FALSE,

    -- Theme-specific fields
    theme_title VARCHAR(500),
    theme_statement TEXT,
    classification VARCHAR(100),
    deal_context VARCHAR(255),
    metadata_insights TEXT,
    primary_quote TEXT,
    secondary_quote TEXT,
    supporting_finding_ids TEXT,
    company_ids TEXT,

    -- Strategic Alert fields
    alert_title VARCHAR(500),
    alert_statement TEXT,
    alert_classification VARCHAR(100),
    strategic_implications TEXT,
    primary_alert_quote TEXT,
    secondary_alert_quote TEXT,
    supporting_alert_finding_ids TEXT,
    alert_company_ids TEXT,

    -- Common fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_stage4_themes_client_id ON stage4_themes(client_id);
CREATE INDEX idx_stage4_themes_theme_id ON stage4_themes(theme_id);
CREATE INDEX idx_stage4_themes_theme_type ON stage4_themes(theme_type);
CREATE INDEX idx_stage4_themes_competitive_flag ON stage4_themes(competitive_flag);

-- Recreate the summary view
CREATE VIEW stage4_themes_summary AS
SELECT 
    client_id,
    theme_type,
    COUNT(*) as theme_count,
    COUNT(CASE WHEN competitive_flag = true THEN 1 END) as competitive_count,
    MIN(created_at) as earliest_theme,
    MAX(created_at) as latest_theme
FROM stage4_themes
GROUP BY client_id, theme_type
ORDER BY client_id, theme_type; 