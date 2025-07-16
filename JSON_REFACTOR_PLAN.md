# VOC Pipeline JSON Refactor Plan

## Overview
Refactor the entire VOC pipeline to use JSON as the canonical exchange format for:
- Internal data processing
- LLM input/output
- Supabase storage (JSONB columns)
- Only use CSV for final business exports

## Benefits
- More robust LLM interactions
- Better data structure flexibility
- Easier debugging and development
- Type-safe operations
- Better error handling

## Implementation Steps

### 1. Stage 3 Output Refactor
- Update `stage3_findings_analyzer.py` to output JSON instead of CSV
- Create JSON schema for findings data
- Update database integration to handle JSON findings

### 2. Stage 4 Input/LLM/Output Refactor
- Update `stage4_theme_analyzer.py` to:
  - Accept JSON input from Stage 3
  - Send JSON prompts to LLM
  - Parse JSON responses from LLM
  - Output JSON themes and alerts
- Update database schema to use JSONB for themes and alerts

### 3. Supabase Schema Updates
- Modify `stage3_findings` table to use JSONB for findings data
- Modify `stage4_themes` table to use JSONB for themes and alerts
- Update database integration methods

### 4. LLM Prompt Updates
- Update all LLM prompts to request JSON output
- Add JSON schema validation
- Improve error handling for malformed JSON

### 5. CSV Export Layer
- Create JSON-to-CSV export functions for business users
- Maintain backward compatibility for existing workflows

## File Changes Required

### Core Files
- `stage3_findings_analyzer.py` - JSON output
- `stage4_theme_analyzer.py` - JSON input/output
- `supabase_database.py` - JSONB schema updates
- `database_integration.py` - JSON methods

### Schema Files
- `complete_stage3_findings_schema.sql` - JSONB columns
- `fix_stage4_themes_schema.sql` - JSONB columns

### Export Files
- `export_findings_json.py` - JSON export utilities
- New CSV export utilities

## Implementation Order
1. Update Supabase schema with JSONB columns
2. Refactor Stage 3 to output JSON
3. Refactor Stage 4 to handle JSON input/output
4. Update database integration methods
5. Create export utilities
6. Test end-to-end workflow

## JSON Schemas

### Stage 3 Findings Schema
```json
{
  "findings": [
    {
      "finding_id": "string",
      "finding_statement": "string",
      "finding_category": "string",
      "impact_score": "number",
      "confidence_score": "number",
      "supporting_quotes": ["string"],
      "companies_mentioned": ["string"],
      "created_at": "datetime"
    }
  ],
  "metadata": {
    "total_findings": "number",
    "analysis_date": "datetime",
    "source_data": "string"
  }
}
```

### Stage 4 Themes Schema
```json
{
  "themes": [
    {
      "theme_id": "string",
      "theme_name": "string",
      "theme_description": "string",
      "strategic_importance": "string",
      "action_items": ["string"],
      "related_findings": ["string"]
    }
  ],
  "alerts": [
    {
      "alert_id": "string",
      "alert_type": "string",
      "alert_message": "string",
      "priority": "string",
      "recommended_actions": ["string"]
    }
  ],
  "metadata": {
    "total_themes": "number",
    "total_alerts": "number",
    "analysis_date": "datetime"
  }
}
``` 