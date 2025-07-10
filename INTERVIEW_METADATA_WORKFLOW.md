# Interview Metadata Workflow Guide

## Overview

This workflow allows you to assign Interview IDs to quotes and map them to company/interviewee metadata for proper attribution in findings. This is especially useful when the transcript data doesn't contain company/interviewee information.

## Components

### 1. Metadata CSV (`interviewee_metadata.csv`)
Contains the mapping between interview IDs and company/interviewee information:
```csv
interview_id,interviewee_name,company
1,Company A Interviewee 1,Company A
2,Company B Interviewee 2,Company B
3,Company C Interviewee 1,Company C
...
```

### 2. Metadata Loader (`interviewee_metadata_loader.py`)
Handles loading and querying the metadata:
- Loads CSV file
- Provides lookup functions
- Validates interview IDs
- Returns company/interviewee information

### 3. Stage 3 Integration
The Stage 3 findings analyzer now includes:
- Metadata loader initialization
- Interview attribution extraction from quotes
- Pattern-based attribution mapping
- Enhanced finding generation with proper attribution

## Usage Workflow

### Step 1: Prepare Your Metadata
1. Create or update `interviewee_metadata.csv` with your actual interview data
2. Ensure each interview has a unique ID
3. Include company and interviewee names

### Step 2: Add Interview IDs to Quotes
When processing quotes, add an `interview_id` field to each quote. You can:
- Extract from response_id (as shown in `add_interview_ids.py`)
- Map based on your interview tracking system
- Assign manually if needed

### Step 3: Run Stage 3 Analysis
The system will automatically:
- Load metadata from CSV
- Map quotes to companies/interviewees via interview_id
- Generate findings with proper attribution
- Export findings with correct company/interviewee names

## Example Output

### Before (Generic Attribution)
```csv
Finding_ID,Finding_Statement,Interview_Company,Interviewee_Name
F1,Product accuracy is critical...,Rev,Multiple
F2,Implementation speed matters...,Rev,Multiple
```

### After (Proper Attribution)
```csv
Finding_ID,Finding_Statement,Interview_Company,Interviewee_Name
F1,Product accuracy is critical...,Company A,Company A Interviewee 1
F2,Implementation speed matters...,Company B,Company B Interviewee 2
```

## Key Benefits

1. **Proper Attribution**: Findings show actual companies and interviewees
2. **Flexible Mapping**: Easy to update metadata without reprocessing quotes
3. **Scalable**: Works with any number of interviews/companies
4. **Fallback Support**: Gracefully handles missing or invalid interview IDs

## Database Schema Requirements

To fully implement this workflow, you'll need to add an `interview_id` field to your quotes table:

```sql
ALTER TABLE stage2_response_labeling ADD COLUMN interview_id INTEGER;
```

## Testing the Workflow

Run the test script to see the mapping in action:
```bash
python add_interview_ids.py
```

This will show how quotes are mapped to companies and interviewees.

## Next Steps

1. **Add interview_id to your database schema**
2. **Update your quote processing to include interview_id**
3. **Replace placeholder metadata with real data**
4. **Run Stage 3 to generate findings with proper attribution**

## Files Created

- `interviewee_metadata.csv` - Sample metadata mapping
- `interviewee_metadata_loader.py` - Metadata loading and querying
- `add_interview_ids.py` - Test script for the workflow
- `INTERVIEW_METADATA_WORKFLOW.md` - This guide

## Integration Points

The workflow integrates with:
- Stage 3 findings analyzer (`stage3_findings_analyzer.py`)
- Export script (`export_improved_findings.py`)
- Database operations (`supabase_database.py`)

All components now support the interview_id → company/interviewee mapping for proper attribution in findings. 